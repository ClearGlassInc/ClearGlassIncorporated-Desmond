import re
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
    assert "IntersectionObserver" in runtime
    assert '(hover: none) and (pointer: coarse)' in runtime
    assert "window.innerWidth <= 820" in runtime
    assert "cgVisualEffects" in runtime
    assert "localStorage" in runtime


def test_cinematic_runtime_avoids_user_agent_and_device_memory_classification() -> None:
    runtime = (ROOT / "assets/js/cinematic-motion.js").read_text(encoding="utf-8")

    assert "navigator.userAgent" not in runtime
    assert "navigator.platform" not in runtime
    assert "navigator.deviceMemory" not in runtime
    assert "touchFirstSmall" in runtime
    assert 'data-cg-performance' in runtime


def test_cinematic_runtime_has_visible_motion_control_and_bounded_frame_rate() -> None:
    runtime = (ROOT / "assets/js/cinematic-motion.js").read_text(encoding="utf-8")

    assert "cg-visual-effects-control" in runtime
    assert "Visual effects: " in runtime
    assert 'data-cg-motion-level' in runtime
    # The guarantee is that the loop runs at a capped 30fps and drops to 15 when
    # the device struggles. The downgrade sits in a closure that captures `this`
    # as `self`, so match either receiver rather than one literal spelling.
    assert re.search(r"\b(?:this|self)\.fps\s*=\s*30\b", runtime)
    assert re.search(r"\b(?:this|self)\.fps\s*=\s*15\b", runtime)
    assert "average > 50" in runtime
    assert "this.downgraded" in runtime


def test_cinematic_runtime_pauses_and_cleans_up_resources() -> None:
    runtime = (ROOT / "assets/js/cinematic-motion.js").read_text(encoding="utf-8")

    assert "visibilitychange" in runtime
    assert "cg-motion-suspended" in runtime
    assert "MutationObserver" in runtime
    assert "cancelAnimationFrame" in runtime
    assert ".disconnect()" in runtime
    assert 'window.addEventListener("pagehide"' in runtime


def test_cinematic_runtime_reapplies_motion_level_after_capability_changes() -> None:
    runtime = (ROOT / "assets/js/cinematic-motion.js").read_text(encoding="utf-8")
    match = re.search(
        r"function onCapabilityChange\(\) \{(?P<body>.*?)\n  \}",
        runtime,
        flags=re.DOTALL,
    )

    assert match, "onCapabilityChange() must remain present"
    body = match.group("body")
    assert "refreshCapabilityState();" in body
    assert "applyMotionLevel();" in body
    assert "if (!explicitPreference)" not in body


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
    version = re.search(r'var VERSION = "cg-v(\d+)";', service_worker)
    assert version, "sw.js must declare a cg-v<N> cache VERSION"
    assert int(version.group(1)) >= 57
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
