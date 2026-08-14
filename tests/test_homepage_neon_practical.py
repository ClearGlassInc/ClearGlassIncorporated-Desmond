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
    stylesheet = (ROOT / "assets/css/neon-practical.css").read_text(encoding="utf-8")

    assert "--cg-neon-period: 5.6s" in stylesheet
    assert "--cg-neon-ease: cubic-bezier(.37, 0, .63, 1)" in stylesheet
    assert "@keyframes cgNeonCore" in stylesheet
    assert "@keyframes cgNeonGas" in stylesheet
    assert "@keyframes cgNeonHalo" in stylesheet
    assert "@keyframes cgNeonSurfaceBounce" in stylesheet
    assert "prefers-reduced-motion: reduce" in stylesheet

    reduced_motion = stylesheet.split("prefers-reduced-motion: reduce", 1)[1]
    assert ".cg-neon-phosphor" in reduced_motion
    assert ".hero-seal-media::after" in reduced_motion


def test_core_pulse_does_not_animate_blur_radius() -> None:
    stylesheet = (ROOT / "assets/css/neon-practical.css").read_text(encoding="utf-8")
    core_keyframes = stylesheet.split("@keyframes cgNeonCore", 1)[1].split("@keyframes", 1)[0]

    assert "filter:" not in core_keyframes
    assert "blur(" not in core_keyframes


def test_physical_tube_edge_remains_unblurred() -> None:
    stylesheet = (ROOT / "assets/css/neon-practical.css").read_text(encoding="utf-8")
    tube_rule = stylesheet.split(".cg-neon-tube-glass {", 1)[1].split("}", 1)[0]

    assert "stroke-width: 8.4" in tube_rule
    assert "blur(" not in tube_rule
    assert "drop-shadow" in tube_rule


def test_neon_has_density_and_dynamic_range_tuning() -> None:
    stylesheet = (ROOT / "assets/css/neon-practical.css").read_text(encoding="utf-8")

    assert "@media (min-resolution: 2dppx)" in stylesheet
    assert "@media (dynamic-range: high)" in stylesheet
    assert "color(display-p3" in stylesheet
