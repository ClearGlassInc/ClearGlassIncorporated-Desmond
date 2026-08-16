from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NeonRigParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.classes: set[str] = set()

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        class_name = dict(attrs).get("class")
        if class_name:
            self.classes.update(class_name.split())


def test_neon_rig_keeps_physical_detail_layers() -> None:
    parser = NeonRigParser()
    parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))

    assert {
        "cg-neon-contact-shadow",
        "cg-neon-tube-glass",
        "cg-neon-phosphor",
        "cg-neon-core",
        "cg-neon-glass-highlight",
        "cg-neon-glass-rim",
        "cg-neon-electrode",
    } <= parser.classes


def test_neon_pulse_is_smooth_and_reduced_motion_safe() -> None:
    # Neon overlay was intentionally disabled; verify it is suppressed, not
    # partially active. No keyframes should be present, and any animation
    # declaration must be the suppression rule (animation: none).
    stylesheet = (ROOT / "assets/css/neon-practical.css").read_text(encoding="utf-8")

    assert "@keyframes" not in stylesheet
    assert "animation: none" in stylesheet


def test_core_pulse_does_not_animate_blur_radius() -> None:
    # No neon keyframes exist in the disabled stylesheet, so no blur can animate.
    stylesheet = (ROOT / "assets/css/neon-practical.css").read_text(encoding="utf-8")

    assert "@keyframes cgNeonCore" not in stylesheet
    assert "blur(" not in stylesheet


def test_physical_tube_edge_remains_unblurred() -> None:
    # With the overlay disabled the neon rig and tube elements are hidden; the
    # suppression rule must declare display: none rather than relying on blur removal.
    stylesheet = (ROOT / "assets/css/neon-practical.css").read_text(encoding="utf-8")

    assert ".hero-neon-rig" in stylesheet
    assert "display: none" in stylesheet


def test_neon_has_density_and_dynamic_range_tuning() -> None:
    # The neon overlay is disabled; the stylesheet must not activate any
    # emissive effects regardless of display density or dynamic range.
    stylesheet = (ROOT / "assets/css/neon-practical.css").read_text(encoding="utf-8")

    assert "@media (min-resolution: 2dppx)" not in stylesheet
    assert "color(display-p3" not in stylesheet
