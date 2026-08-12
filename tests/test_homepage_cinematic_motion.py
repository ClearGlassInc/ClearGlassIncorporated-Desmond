from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_homepage_keeps_existing_future_buttons_entrypoint() -> None:
    homepage = (ROOT / "index.html").read_text(encoding="utf-8")
    assert '<script defer src="/assets/js/future-buttons.js"></script>' in homepage


def test_future_buttons_loader_targets_existing_cinematic_assets() -> None:
    loader = (ROOT / "assets/js/future-buttons.js").read_text(encoding="utf-8")
    assert "loadHomepageCinematicMotion" in loader
    assert '"/assets/css/cinematic-motion.css"' in loader
    assert '"/assets/js/cinematic-motion.js"' in loader
    assert "if (!isHomepage()) return;" in loader

    assert (ROOT / "assets/css/cinematic-motion.css").is_file()
    assert (ROOT / "assets/js/cinematic-motion.js").is_file()


def test_cinematic_motion_remains_accessibility_and_power_aware() -> None:
    stylesheet = (ROOT / "assets/css/cinematic-motion.css").read_text(encoding="utf-8")
    runtime = (ROOT / "assets/js/cinematic-motion.js").read_text(encoding="utf-8")

    assert "prefers-reduced-motion: reduce" in stylesheet
    assert "prefers-reduced-motion: reduce" in runtime
    assert "navigator.connection" in runtime
    assert "navigator.deviceMemory" in runtime
    assert "IntersectionObserver" in runtime


def test_cinematic_runtime_fails_static_on_ios_webkit() -> None:
    runtime = (ROOT / "assets/js/cinematic-motion.js").read_text(encoding="utf-8")

    assert "appleMobile" in runtime
    assert "navigator.maxTouchPoints" in runtime
    assert 'data-cg-cinematic-motion", "ios-stability"' in runtime
    assert "if (appleMobile)" in runtime


def test_homepage_platform_isolates_duplicate_fixed_control_runtimes() -> None:
    runtime = (ROOT / "platform.js").read_text(encoding="utf-8")

    assert "var isHomepage =" in runtime
    assert 'data-cg-home-runtime", "stabilized"' in runtime

    fx_section = runtime.split("advanced motion layer", 1)[1].split("cinematic system", 1)[0]
    assert "if (!isHomepage)" in fx_section
    assert 'fx.src = "fx.js"' in fx_section

    cinematic_section = runtime.split("cinematic system", 1)[1].split("AEGIS-OMEGA control plane", 1)[0]
    assert 'cinematic.src = "/assets/js/cinematic-motion.js"' in cinematic_section
    assert "if (!isHomepage)" not in cinematic_section

    omega_section = runtime.split("AEGIS-OMEGA control plane", 1)[1].split('if ("serviceWorker" in navigator)', 1)[0]
    assert "if (!isHomepage)" in omega_section
    assert 'omega.setAttribute("data-cg-aegis-omega", "true")' in omega_section


def test_homepage_synchronizes_sentinel_modal_with_visible_shell() -> None:
    runtime = (ROOT / "platform.js").read_text(encoding="utf-8")

    assert 'document.getElementById("sentinelShell")' in runtime
    assert 'sentinelShell.querySelector(\'[role="dialog"]\')' in runtime
    assert 'sentinelDialog.setAttribute("aria-modal", String(open))' in runtime
    assert 'sentinelShell.setAttribute("aria-hidden", String(!open))' in runtime
    assert 'attributeFilter: ["hidden"]' in runtime


def test_homepage_runtime_cache_is_invalidated() -> None:
    service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
    assert 'var VERSION = "cg-v55";' in service_worker
    assert '"/platform.js"' in service_worker
    assert '"/stealth-glass.js"' in service_worker


def test_neon_layer_uses_named_restrained_motion_primitives() -> None:
    stylesheet = (ROOT / "assets/css/cinematic-motion.css").read_text(encoding="utf-8")

    for keyframe in (
        "neonPulse",
        "coreBreathe",
        "borderTrace",
        "signalFlicker",
        "gridDrift",
        "scanSweep",
    ):
        assert f"@keyframes {keyframe}" in stylesheet

    assert "html.cg-low-power" in stylesheet
    assert "animation: none !important;" in stylesheet
    assert "pointer-events: none;" in stylesheet
