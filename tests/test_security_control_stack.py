from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_security_controls_share_a_fused_glass_dock() -> None:
    css = (ROOT / "security-stack-fusion.css").read_text(encoding="utf-8")
    aegis = (ROOT / "aegis-glass.js").read_text(encoding="utf-8")
    stealth = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")

    assert "#cg-security-stack" in css
    assert "Security Stack Fusion Dock" in css
    assert "display:flex" in css or "display: flex" in css
    assert "flex-direction:column" in css or "flex-direction: column" in css
    assert "justify-content:flex-end" in css or "justify-content: flex-end" in css
    assert "backdrop-filter:blur(22px)" in css or "backdrop-filter: blur(22px)" in css
    assert "securityStack.appendChild(status)" in aegis
    assert "securityStack.appendChild(stealthButton)" in aegis
    assert "stack.insertBefore(btn, stack.firstChild)" in stealth
    assert "cg-security-dock-mounted" in stealth


def test_security_pills_keep_standalone_fallbacks() -> None:
    css = (ROOT / "security-stack-fusion.css").read_text(encoding="utf-8")
    stealth = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")

    assert "#cg-security-stack #cg-stealth-btn" in css
    assert "#cg-security-stack #aegis-glass-status" in css
    assert "--cg-security-bottom" in css
    assert "--cg-security-edge" in css
    assert "--cg-security-bottom,84px" in stealth
    assert "--cg-security-edge,18px" in stealth


def test_mobile_fusion_dock_reserves_bottom_clearance_and_stays_compact() -> None:
    css = (ROOT / "security-stack-fusion.css").read_text(encoding="utf-8")

    # The dock clears content by reserving bottom padding, not by reserving a
    # right-hand lane -- the lane approach overlapped CTA rows on small screens.
    assert "--cg-mobile-fusion-clearance:84px" in css or "--cg-mobile-fusion-clearance: 84px" in css
    assert "padding-bottom:calc(var(--cg-mobile-fusion-clearance)" in css
    assert "--cg-mobile-fusion-right-lane" not in css
    # Compact corner launcher: under half the viewport so CTA rows stay visible.
    assert "width:min(156px,calc(100vw - 24px))" in css
    assert "body.cg-security-dock-mounted" in css
    assert "#cg-security-stack #aegis-glass-status{display:none!important}" in css
    assert "@media(max-width:720px)" in css
    assert "prefers-reduced-motion:reduce" in css


def test_security_dock_does_not_create_a_blank_right_hand_lane() -> None:
    css = (ROOT / "security-stack-fusion.css").read_text(encoding="utf-8")

    assert "body.cg-security-dock-mounted #cg-neon-aura::after" in css
    assert "display:none!important" in css


def test_scroll_controls_include_top_and_bottom_arrows() -> None:
    css = (ROOT / "fx.css").read_text(encoding="utf-8")
    js = (ROOT / "fx.js").read_text(encoding="utf-8")

    assert "#cg-top,#cg-bottom" in css
    assert "Scroll to bottom" in js
    assert "bottom.innerHTML = \"↓\"" in js
    assert "window.scrollTo({ top: max" in js
