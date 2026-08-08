from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_security_controls_share_a_flex_stack() -> None:
    css = (ROOT / "aegis-glass.css").read_text(encoding="utf-8")
    aegis = (ROOT / "aegis-glass.js").read_text(encoding="utf-8")
    stealth = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")

    assert "#cg-security-stack" in css
    assert "display: flex" in css
    assert "flex-direction: column" in css
    assert "justify-content: flex-end" in css
    assert "gap: 1rem" in css
    assert "backdrop-filter: blur(18px)" in css
    assert "align-self: flex-end" in css
    assert "align-self: center" in css
    assert "securityStack.appendChild(status)" in aegis
    assert "securityStack.appendChild(stealthButton)" in aegis
    assert 'stack.insertBefore(btn, stack.firstChild)' in stealth


def test_security_pills_keep_standalone_fallbacks() -> None:
    css = (ROOT / "aegis-glass.css").read_text(encoding="utf-8")
    stealth = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")

    assert "#aegis-glass-status {" in css
    assert "position: absolute" in css
    assert "--cg-security-bottom,84px" in stealth
    assert "--cg-security-edge,18px" in stealth


def test_mobile_fusion_dock_reserves_control_lane_and_sentinel_clearance() -> None:
    css = (ROOT / "aegis-glass.css").read_text(encoding="utf-8")

    assert "Aegis × Sentinel Fusion Dock" in css
    assert "--cg-mobile-fusion-right-lane: 76px" in css
    assert "grid-template-columns: minmax(0, 1fr) auto" in css
    assert "right: max(var(--cg-mobile-fusion-right-lane), env(safe-area-inset-right))" in css
    assert "--cg-mobile-fusion-clearance: 92px" in css
    assert ".sentinel-hero" in css
    assert "scroll-margin-block-end" in css
    assert "touch-action: manipulation" in css
    assert "prefers-reduced-motion: reduce" in css
