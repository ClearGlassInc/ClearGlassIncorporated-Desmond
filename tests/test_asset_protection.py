from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "asset-protection.js").read_text(encoding="utf-8")


def test_protection_is_opt_in_and_does_not_disable_global_selection() -> None:
    assert "[data-cg-protected]" in SCRIPT
    assert "document.body.style.userSelect" not in SCRIPT
    assert 'closest("input,textarea,select,[contenteditable=true]")' in SCRIPT


def test_watermark_is_non_interactive_and_print_persistent() -> None:
    assert "[data-cg-watermark]::after" in SCRIPT
    assert "pointer-events:none" in SCRIPT
    assert "@media print" in SCRIPT


def test_asset_protection_remains_idempotent() -> None:
    assert "if (window.__cgAssetProtection) return" in SCRIPT
    assert 'getElementById("cg-asset-protection-styles")' in SCRIPT


def test_class_based_copy_friction_and_watermark_are_available() -> None:
    assert ".protected,.protected *" in SCRIPT
    assert ".protected-watermark::after" in SCRIPT
    assert "ClearGlassInc. • Confidential • © 2026" in SCRIPT
    assert ".blur-preview:hover,.blur-preview:focus-within" in SCRIPT
    assert "prefers-reduced-motion:reduce" in SCRIPT


def test_protected_shortcuts_and_session_token_preserve_form_use() -> None:
    assert '["c", "u", "s", "p"].indexOf(key)' in SCRIPT
    assert "if (!isCopyShortcut || isEditable(e.target)) return" in SCRIPT
    assert 'meta[name="session-watermark"]' in SCRIPT
    assert "window.crypto.getRandomValues" in SCRIPT
