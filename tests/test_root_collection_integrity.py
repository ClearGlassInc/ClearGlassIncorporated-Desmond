"""The root suite must still collect when the commerce extras are absent.

`pyproject.toml` points `testpaths` at `clearglass-commerce/control-plane/tests`,
but the root `[test]` extra installs neither `sqlalchemy` nor `stripe` — only
`clearglass-commerce/control-plane/requirements.txt` does. So a commerce test
module that reaches the database stack at import time takes the *entire* root
suite down with it: pytest aborts the session, and the other ~1,940 tests never
run. Nothing is reported as failed, which is what makes it easy to miss.

This has now happened twice and grew in between — three modules, then five, one
of them only transitively through `app.main`. A static scan for `import
sqlalchemy` would not have caught that transitive case, so this reproduces the
real condition instead: collect the commerce testpath in a subprocess with the
commerce-only distributions hidden from the import system.

Where this actually earns its keep: a contributor (or the commerce CI job) has
the full stack installed, so collection succeeds locally and the breakage is
invisible to them — it only appears in the root job, which has a thinner
dependency set. This test makes that second environment observable from the
first. It cannot rescue a root run that has already aborted, because that
aborts this module too; it exists to stop the breakage being *introduced*.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMERCE_TESTS = ROOT / "clearglass-commerce/control-plane/tests"

# Installed by clearglass-commerce/control-plane/requirements.txt, never by the
# root `[test]` extra. Keep in sync if the root extra starts shipping one.
COMMERCE_ONLY_DISTRIBUTIONS = ("sqlalchemy", "stripe")

_COLLECT = textwrap.dedent(
    """
    import sys

    BLOCKED = {blocked!r}


    class _HideCommerceExtras:
        \"\"\"Make the commerce-only distributions look uninstalled.\"\"\"

        def find_spec(self, fullname, path=None, target=None):
            if fullname.split(".")[0] in BLOCKED:
                raise ModuleNotFoundError(f"No module named {{fullname!r}}")
            return None


    for name in list(sys.modules):
        if name.split(".")[0] in BLOCKED:
            del sys.modules[name]

    sys.meta_path.insert(0, _HideCommerceExtras())

    import pytest

    raise SystemExit(
        pytest.main(["--collect-only", "-q", "-p", "no:cacheprovider", {target!r}])
    )
    """
)


def test_commerce_testpath_collects_without_the_commerce_extras() -> None:
    """Guarded modules skip; an unguarded import aborts the whole root suite."""
    assert COMMERCE_TESTS.is_dir(), f"missing commerce testpath: {COMMERCE_TESTS}"

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            _COLLECT.format(
                blocked=COMMERCE_ONLY_DISTRIBUTIONS,
                target=str(COMMERCE_TESTS),
            ),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )

    # pytest exits 2 on a collection error and 5 when everything was skipped.
    # 5 is legitimate here: with the database stack hidden, every guarded module
    # may skip. 2 is the regression this test exists to catch.
    assert result.returncode in (0, 5), (
        "Root pytest collection breaks when the commerce extras are absent, so "
        "the entire root suite would abort instead of running.\n"
        'Guard the offending module with pytest.importorskip("sqlalchemy") '
        "before it reaches the database stack — a transitive import through "
        "app.main counts, which is why this collects rather than scanning source."
        f"\n\nexit={result.returncode}\n{result.stdout[-3000:]}\n{result.stderr[-2000:]}"
    )
