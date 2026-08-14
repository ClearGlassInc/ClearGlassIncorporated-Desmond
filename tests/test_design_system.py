"""Gates for the ClearGlass Interface System.

The site's visual and keyboard consistency is enforced by convention nowhere and
by these tests everywhere. They cover three things convention has already failed
at once in this repo:

  * a page shipping without the shared design system or navigation,
  * a page shipping without a bypass link because it happens to use the *other*
    navigation system (``control-surface.js`` suppresses ``nav.js`` on purpose),
  * the injected navigation quietly losing a piece of its keyboard contract.

The browser-level behaviour (focus trap, Escape, command palette) is verified by
``tests/browser/*.mjs`` under Playwright; these tests pin the source contract so
a regression is caught even where no browser is available.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NAV_JS = ROOT / "nav.js"
A11Y_JS = ROOT / "cg-a11y.js"


def _load_design_system():
    spec = importlib.util.spec_from_file_location(
        "cg_design_system", ROOT / "tools" / "design_system.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["cg_design_system"] = module
    spec.loader.exec_module(module)
    return module


ds = _load_design_system()


# ── site-wide adoption ───────────────────────────────────────────────────────

def test_every_public_route_loads_the_design_system_and_keyboard_contract():
    """The gate itself: no route may drift out of the shared system."""
    stale = []
    for page in ds.pages():
        row = ds.audit_page(page)
        gaps = [
            name
            for name, missing in (
                ("design-system css", row["missing_css"]),
                ("global nav", row["missing_nav"]),
                ("a11y contract", row["missing_a11y"]),
            )
            if missing
        ]
        if gaps:
            stale.append(f"{row['path']}: missing {', '.join(gaps)}")
    assert not stale, "Run `python3 tools/design_system.py`:\n" + "\n".join(stale)


def test_indexable_routes_carry_social_metadata():
    missing = [
        row["path"]
        for page in ds.pages()
        if (row := ds.audit_page(page))["missing_twitter"] and row["can_build_twitter"]
    ]
    assert not missing, "Run `python3 tools/design_system.py`: " + ", ".join(missing)


def test_generator_is_idempotent():
    """A second pass must find nothing to do, or the tool rewrites files forever.

    ``fix_page`` writes, so every page is snapshotted and restored. Without that
    this test *repairs* a stale tree as a side effect — it silently edited two
    pages the first time it ran against drifted content, which is exactly the
    kind of hidden mutation a test must never perform.
    """
    for page in ds.pages():
        before = page.read_text(encoding="utf-8", errors="replace")
        try:
            changes = ds.fix_page(page)
        finally:
            if page.read_text(encoding="utf-8", errors="replace") != before:
                page.write_text(before, encoding="utf-8")
        assert changes == [], (
            f"{ds.rel_path(page)} still needs {changes}; "
            "run `python3 tools/design_system.py` and commit the result"
        )


def test_every_exemption_names_a_real_page_and_a_reason():
    """An exemption that outlives its page becomes silent, permanent drift."""
    for path, reason in {**ds.EXEMPT, **ds.NAV_EXEMPT}.items():
        assert (ROOT / path).exists(), f"exemption points at a missing page: {path}"
        assert len(reason) > 15, f"exemption for {path} needs a real reason"
    for directory, reason in ds.EXEMPT_DIRS.items():
        assert (ROOT / directory).is_dir(), f"exempt directory is gone: {directory}"
        assert len(reason) > 15, f"exempt directory {directory} needs a real reason"


def test_discovery_is_recursive_so_new_sections_are_covered():
    """An allow-list of known subdirectories is how a whole section gets missed.

    streaming-growth-command-center/ shipped outside every gate because the page
    walker only looked in four hard-coded folders.
    """
    found = {ds.rel_path(p) for p in ds.pages()}
    assert "streaming-growth-command-center/index.html" in found
    assert "legal/privacy.html" in found
    # Exempt subtrees are still discovered — they are classified, not skipped,
    # so the report can show them rather than pretending they do not exist.
    assert any(p.startswith("operations/") for p in found)


def test_twitter_cards_are_never_invented():
    """A card must be derived from metadata the page already declares."""
    page_without_metadata = "<html><head><title></title></head><body></body></html>"
    assert ds.twitter_block(page_without_metadata) == ""

    real = (
        '<html><head><title>Pricing</title>'
        '<meta name="description" content="Fixed-fee engagements.">'
        "</head><body></body></html>"
    )
    block = ds.twitter_block(real)
    assert "Fixed-fee engagements." in block
    assert "summary_large_image" in block


# ── navigation keyboard contract (source-level) ──────────────────────────────

@pytest.fixture(scope="module")
def nav_source() -> str:
    return NAV_JS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def a11y_source() -> str:
    return A11Y_JS.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "needle, why",
    [
        ("cg-skip", "the bypass link is the first WCAG 2.4.1 requirement"),
        ('aria-current', "the active route must be exposed, not just coloured"),
        ("Escape", "modal surfaces must close on Escape"),
        ("trapFocus", "the mobile drawer and palette must trap focus"),
        ("aria-expanded", "the products disclosure must expose its state"),
        ("prefers-reduced-motion", "motion must be optional"),
    ],
)
def test_nav_keeps_its_keyboard_contract(nav_source, needle, why):
    assert needle in nav_source, f"nav.js lost {needle}: {why}"


def test_nav_closed_menu_leaves_the_tab_order(nav_source):
    """visibility:hidden is what removes the 60+ catalog links from tab order.

    Without it the closed mega-menu stays focusable and a keyboard user has to
    tab through the entire product catalog to reach the page.
    """
    assert "visibility:hidden" in nav_source


def test_only_one_module_claims_cmd_k():
    """Cmd/Ctrl+K must open exactly one overlay.

    Three modules have wanted this shortcut at various points: nav.js's own
    palette (removed — global-nav-search.js supersedes it), global-nav-search.js
    (the owner: discoverable control in the nav, plus "/"), and aegis-omega.js.
    platform.js loads the latter two together, so both fired on one keystroke
    across all 43 pages that load it until aegis-omega learned to yield.

    Scope matters: other modules bind Cmd/Ctrl+K too (control-surface.js,
    guardian-command.js), but they do not collide because they never co-mount
    with the search — control-surface.js suppresses the primary nav, and the
    search only attaches where one exists. Verified in a browser: pricing.html
    opens exactly one overlay. So this test checks only the modules that
    platform.js loads *together*, which is where the collision was real.
    """
    platform = (ROOT / "platform.js").read_text(encoding="utf-8", errors="replace")
    co_mounted = {
        f"{name}.js"
        for name in re.findall(r'platformAsset\("([\w-]+)\.js"\)', platform)
    }
    assert "global-nav-search.js" in co_mounted, "search is no longer loaded by platform.js"

    binder = re.compile(r"(?:metaKey|ctrlKey)[\s\S]{0,120}?[\"']k[\"']", re.I)
    offenders = []
    for name in sorted(co_mounted - {"global-nav-search.js"}):
        module = ROOT / name
        if not module.exists():
            continue
        source = module.read_text(encoding="utf-8", errors="replace")
        if binder.search(source) and "__cgGlobalNavSearch" not in source:
            offenders.append(name)
    assert not offenders, (
        f"{offenders} bind Cmd/Ctrl+K and are loaded by platform.js alongside "
        "global-nav-search.js, so both overlays open on one keystroke. Yield by "
        "returning early when window.__cgGlobalNavSearch is set."
    )


def test_nav_no_longer_ships_a_competing_palette(nav_source):
    assert "installCommandPalette" not in nav_source
    assert "cg-palette" not in nav_source


def test_a11y_module_covers_both_navigation_systems(a11y_source):
    """control-surface.js suppresses nav.js; its containers must still be marked."""
    assert "cgcs-menu" in a11y_source and "cgcs-bar" in a11y_source
    assert "cg-global-nav" in a11y_source


def test_a11y_module_is_idempotent_with_nav(a11y_source):
    """Both scripts inject a skip link; loading both must not produce two."""
    assert 'querySelector(".cg-skip")' in a11y_source


def test_a11y_module_does_not_fabricate_a_main_landmark(a11y_source):
    """Promoting a hero <header> to role=main would mislabel a partial region.

    The module resolves a skip *target* on pages without <main>, but must not
    claim a landmark it cannot honestly identify.
    """
    assert 'setAttribute("role", "main")' not in a11y_source


# ── content honesty ──────────────────────────────────────────────────────────

# Two distinct failures, both of which borrow authority the company does not
# have: a grade claim benchmarked against a state actor, and markings that
# imitate a government classification caveat.
#
# Deliberately NOT matched: "UNCLASSIFIED / NON-CLASSIFIÉ" banners (they assert
# the absence of classification and are labelled demo instances), and ordinary
# prose — "classified as harmful", "hashed, classified and deduplicated",
# "open, unclassified doctrine". Those are accurate uses of an ordinary English
# word, and a gate that flags them would be turned off within a week.
#
# A quoted "defense-grade" is also allowed: blog/clearglass-platform-audit-2026
# uses it in scare quotes to argue *against* the term, which is commentary on
# the phrase rather than a claim made in the company's own voice.
PROHIBITED = re.compile(
    r"(?<![\"“])\b(?:NSA|military|defense|defence|government)-grade\b"
    r"|\bgovernment-affiliated\b"
    r"|(?<!UN)(?<!NON-)\bCLASSIFIED\b\s*(?:·|//|<span>·</span>|BRIEFING|COMMAND)"
    r"|\bEYES ONLY\b"
    r"|//\s*(?:SI|NF|NOFORN|SCI)\b",
    re.I,
)


def test_no_prohibited_assurance_language_in_public_pages():
    """The site must not borrow authority it does not have.

    This caught five real instances when first written: a "military-grade"
    product claim, two "CLASSIFIED · COMMAND INTERFACE" chrome labels, a
    "CG//SI//NF" caveat imitating US intelligence control markings, and an
    "EYES ONLY" briefing header.
    """
    offenders = []
    for page in ds.pages():
        row = ds.audit_page(page)
        if row["noindex"] or row["exempt"]:
            continue
        text = page.read_text(encoding="utf-8", errors="replace")
        for match in PROHIBITED.finditer(text):
            offenders.append(f"{row['path']}: {match.group(0)!r}")
    assert not offenders, "prohibited assurance language: " + "; ".join(offenders)
