import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CSS = ROOT / "aegis-omega.css"
JS = ROOT / "aegis-omega.js"


def test_capability_layer_ships_and_is_precached() -> None:
    platform = (ROOT / "platform.js").read_text(encoding="utf-8")
    sw = (ROOT / "sw.js").read_text(encoding="utf-8")

    assert CSS.exists()
    assert JS.exists()
    assert 'platformAsset("aegis-omega.css")' in platform
    assert 'platformAsset("aegis-omega.js")' in platform
    # Returning visitors must not keep a service-worker cache that predates the
    # capability layer, so both assets are precached behind a bumped VERSION.
    assert '"/aegis-omega.css"' in sw
    assert '"/aegis-omega.js"' in sw
    # Pin the floor, not the exact value. VERSION is bumped on every deploy that
    # touches many pages (see CLAUDE.md), so an exact match fails on each
    # legitimate bump while proving nothing extra — what matters is that the
    # cache generation is at or past the one that introduced this layer.
    version = re.search(r'var VERSION = "cg-v(\d+)"', sw)
    assert version, "sw.js must declare a cg-v<N> cache VERSION"
    assert int(version.group(1)) >= 47


def test_capability_layer_is_fault_contained() -> None:
    platform = (ROOT / "platform.js").read_text(encoding="utf-8")
    javascript = JS.read_text(encoding="utf-8")

    # A decorative layer must never become a hard dependency for navigation:
    # it loads deferred, and a load failure degrades instead of throwing.
    assert "omega.defer = true" in platform
    assert 'document.documentElement.setAttribute("data-aegis-omega", "degraded")' in platform
    # Re-entry guard: a double load must not mount two control planes.
    assert "window.ClearGlassAEGIS&&window.ClearGlassAEGIS.version==='OMEGA'" in javascript


def test_capability_layer_uses_safe_dom_apis_only() -> None:
    javascript = JS.read_text(encoding="utf-8")

    for unsafe in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"):
        assert unsafe not in javascript, f"unsafe DOM API in aegis-omega.js: {unsafe}"
    # Command palette results are rebuilt from text nodes, never markup strings.
    assert "list.replaceChildren()" in javascript
    assert "createTextNode" in javascript
    # Palette only ever navigates same-origin URLs it resolved itself.
    assert "url.origin!==location.origin" in javascript


def test_capability_layer_respects_reduced_motion_and_device_budget() -> None:
    css = CSS.read_text(encoding="utf-8")
    javascript = JS.read_text(encoding="utf-8")

    assert "@media(prefers-reduced-motion:reduce)" in css
    assert "(prefers-reduced-motion: reduce)" in javascript
    # Reduced motion collapses the tier rather than merely skipping one effect.
    assert "if(reduceQuery.matches||saveData) return 'MINIMAL'" in javascript
    # Effects suspend when offscreen and when the document is hidden.
    assert "IntersectionObserver" in javascript
    assert "visibilitychange" in javascript
    assert "animation-play-state:paused" in css


def test_command_palette_is_keyboard_accessible() -> None:
    javascript = JS.read_text(encoding="utf-8")

    assert "'role','dialog'" in javascript
    assert "'aria-modal','true'" in javascript
    assert "event.key==='Escape'" in javascript
    # Focus is returned to the invoking element when the palette closes.
    assert "previousFocus.focus()" in javascript


def test_decorative_telemetry_makes_no_operational_claims() -> None:
    javascript = JS.read_text(encoding="utf-8")

    # The rail is presentation only. It must say so, stay out of the a11y tree,
    # and never assert live security or infrastructure state.
    assert "not infrastructure or security telemetry" in javascript
    assert "telemetry.setAttribute('aria-hidden','true')" in javascript
    for claim in ("AUTHENTICATING", "SECURITY SCANNING", "THREATS BLOCKED", "ENCRYPTED"):
        assert claim not in javascript, f"fabricated operational claim in telemetry: {claim}"
