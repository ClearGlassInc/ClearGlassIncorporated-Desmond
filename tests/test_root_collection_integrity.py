"""The root suite must still collect when the commerce extras are absent.

`pyproject.toml` points `testpaths` at `clearglass-commerce/control-plane/tests`,
but the root `[test]` extra installs neither `sqlalchemy` nor `stripe` — only the
commerce workflow installs those. So a commerce test module that reaches the
database stack at import time takes the *entire* root suite down with it:
collection aborts, and pytest reports an error instead of running the other
~1,850 tests. Nothing is marked failed, so the loss is easy to miss.

That is not hypothetical. Three modules imported `sqlalchemy` at module scope —
one of them only transitively, through `app.main` — and the root gate collected
zero tests until they were guarded with `pytest.importorskip`.

A static scan for `import sqlalchemy` would not have caught the transitive case,
so this reproduces the real condition instead: collect the commerce testpath in a
subprocess with the commerce-only distributions hidden from the import system. A
guarded module skips; an unguarded one errors, exactly as the root gate would.
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
    # 5 is a legitimate outcome here: with the database stack hidden, every
    # guarded module may skip. 2 is the regression this test exists to catch.
    assert result.returncode in (0, 5), (
        "Root pytest collection breaks when the commerce extras are absent, so "
        "the entire root suite would abort instead of running.\n"
        "Guard the offending module with pytest.importorskip(\"sqlalchemy\") "
        "before it reaches the database stack — see tests/test_root_collection_"
        "integrity.py for why a transitive import counts.\n\n"
        f"exit={result.returncode}\n{result.stdout[-3000:]}\n{result.stderr[-2000:]}"
    )
