import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_security_controls_render_as_one_control_station() -> None:
    css = (ROOT / "security-stack-fusion.css").read_text(encoding="utf-8")
    stealth = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")

    assert "cg-assistant-panel" in stealth
    assert "cg-assistant-launcher" in stealth
    assert "ClearGlass Station" in stealth
    assert "Control Station" in stealth
    assert "<strong>Action 1</strong>" not in stealth
    assert "<strong>Action 2</strong>" not in stealth
    assert "#cg-security-stack.is-expanded #cg-assistant-launcher" in css
    assert "width:100%!important" in css
    assert "margin-bottom:-1px!important" in css


def test_aegis_cannot_pull_stealth_out_of_the_station() -> None:
    aegis = (ROOT / "aegis-glass.js").read_text(encoding="utf-8")
    stealth = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")

    assert "assistantActions" in aegis
    assert "assistantStatusSlot" in aegis
    assert "(assistantStatusSlot || securityStack).appendChild(status)" in aegis
    assert "if (stealthButton) securityStack.appendChild(stealthButton)" not in aegis
    assert "adoptUnifiedControls(panel)" in stealth
    assert 'actions.insertBefore(stealthButton, firstCapability)' in stealth


def test_scattered_legacy_controls_are_quarantined() -> None:
    css = (ROOT / "security-stack-fusion.css").read_text(encoding="utf-8")
    stealth = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")

    assert "oldStationPattern" in stealth
    assert "stealth\\s*glass" in stealth
    assert "action\\s*1" in stealth
    assert "move\\s*up" in stealth
    assert "floatingHost" in stealth
    assert "hidden-by-control-station" in stealth
    assert "body.cg-security-dock-mounted .sentinel-launcher" in css
    assert "body.cg-security-dock-mounted #sentinelLauncher" in css


def test_station_owns_page_navigation_without_duplicate_floaters() -> None:
    css = (ROOT / "security-stack-fusion.css").read_text(encoding="utf-8")
    stealth = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")
    fx = (ROOT / "fx.js").read_text(encoding="utf-8")

    assert 'id="cg-station-top"' in stealth
    assert 'id="cg-station-bottom"' in stealth
    assert 'stationScroll("top")' in stealth
    assert 'stationScroll("bottom")' in stealth
    assert "body.cg-security-dock-mounted #cg-top" in css
    assert "body.cg-security-dock-mounted #cg-bottom" in css
    assert "Scroll to bottom" in fx


def test_mobile_station_is_safe_area_aware_and_contained() -> None:
    css = (ROOT / "security-stack-fusion.css").read_text(encoding="utf-8")

    assert "@media(max-width:720px)" in css
    assert "env(safe-area-inset-bottom)" in css
    assert "width:min(272px,calc(100vw - 24px))!important" in css
    assert "max-height:min(450px,calc(100dvh - 112px))!important" in css
    assert "#cg-assistant-launcher{width:154px!important" in css
    assert "prefers-reduced-motion:reduce" in css


def test_station_scroll_collision_work_is_bounded() -> None:
    stealth = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")

    # What has to hold is that a scroll-time collision check does bounded work:
    # candidates come from the narrow precomputed selector, and the hot path does
    # no per-node style resolution. Pinning the exact call site made this fail
    # when the query moved into refreshCollisionTargets() — which caches the list
    # once instead of re-querying per check, i.e. a tighter bound, not a lost one.
    assert "COLLISION_TARGET_SELECTOR" in stealth
    assert "document.querySelectorAll(COLLISION_TARGET_SELECTOR)" in stealth

    # Slice on the bare function name: `scheduleCollisionCheck` later took an
    # `immediate` parameter, and a boundary spelled with "()" stopped matching —
    # which silently extended this slice to end-of-file and swept in build()'s
    # perfectly legitimate queries.
    collision = stealth.split("function avoidCTAOverlap(", 1)[1].split("function scheduleCollisionCheck(", 1)[0]
    assert "collisionTargets" in collision, "hot path must walk the cached target list"
    assert "querySelectorAll" not in collision, "no ad-hoc DOM query per collision check"
    assert "getComputedStyle" not in collision, "no per-node style resolution on scroll"

    scheduler = stealth.split("function scheduleCollisionCheck(", 1)[1].split("function scheduleLegacyRefresh", 1)[0]
    # Coalescing is the guarantee; the scheduler may guard on more than the rAF
    # handle (it now also holds a debounce timer), so assert the early return
    # covers collisionRaf rather than pinning one exact condition.
    assert re.search(r"if \([^)]*\bcollisionRaf\b[^)]*\) return;", scheduler)


def test_station_observer_ignores_animation_class_churn() -> None:
    stealth = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")

    observer = stealth.split("legacyObserver = new MutationObserver", 1)[1]
    # The point of the filter is which attributes are watched, not the exact
    # literal: "class" must stay out, or every animation frame that toggles a
    # class re-triggers the observer. Other dialog-state attributes may be added.
    attribute_filter = observer.split("attributeFilter:", 1)[1].split("]", 1)[0]
    assert '"open"' in attribute_filter
    assert '"aria-modal"' in attribute_filter
    assert '"class"' not in attribute_filter, "watching class re-triggers on animation churn"
    assert "scheduleLegacyRefresh(panel, stack)" in observer
