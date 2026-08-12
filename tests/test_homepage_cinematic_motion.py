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
