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
    """The scroll path must reuse a cached target list, never re-query the DOM.

    The collision targets are resolved once by refreshCollisionTargets() and
    cached, so avoidCTAOverlap() — which runs per animation frame while
    scrolling — only measures nodes it already holds.
    """
    stealth = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")

    assert "COLLISION_TARGET_SELECTOR" in stealth
    refresh = stealth.split("function refreshCollisionTargets()", 1)[1].split("function visibleRect", 1)[0]
    assert "document.querySelectorAll(COLLISION_TARGET_SELECTOR)" in refresh

    collision = stealth.split("function avoidCTAOverlap()", 1)[1].split("function scheduleCollisionCheck(", 1)[0]
    assert "collisionTargets" in collision
    assert "querySelectorAll" not in collision
    assert "window.getComputedStyle(node)" not in collision

    scheduler = stealth.split("function scheduleCollisionCheck(", 1)[1].split("function scheduleLegacyRefresh", 1)[0]
    # Coalesced by both an in-flight frame and a throttle timer.
    assert "if (collisionRaf || collisionTimer) return;" in scheduler
    assert "COLLISION_INTERVAL_MS" in scheduler


def test_station_observer_ignores_animation_class_churn() -> None:
    stealth = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")

    observer = stealth.split("legacyObserver = new MutationObserver", 1)[1]
    attribute_filter = observer.split("attributeFilter: [", 1)[1].split("]", 1)[0]
    # "class" churns on every animation frame; observing it would rebuild the
    # station continuously. Modal/visibility state is what must be watched.
    assert '"class"' not in attribute_filter
    for attribute in ('"open"', '"aria-modal"'):
        assert attribute in attribute_filter
    assert "scheduleLegacyRefresh(panel, stack)" in observer
