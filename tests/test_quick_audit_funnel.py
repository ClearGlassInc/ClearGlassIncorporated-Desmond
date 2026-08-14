"""Integrity gates for the Ontario Security Quick-Audit funnel."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OFFER = ROOT / "offers" / "security-quick-audit.html"
SAMPLE = ROOT / "offers" / "security-quick-audit-sample-report.html"
METHOD = ROOT / "offers" / "security-quick-audit-methodology.html"
THANKS = ROOT / "offers" / "thank-you.html"
STRIPE_URL = "https://buy.stripe.com/8x2eVe7ZG0mFam00LG4Ni03"
SEARCH_CONSOLE_TOKEN = "23RWyXWkoxqgArev8achU8IfVxYC5EIUAYBsuTYKLFM"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _json_ld(path: Path) -> list[dict]:
    blocks = re.findall(
        r'<script\s+type="application/ld\+json">(.*?)</script>',
        _text(path),
        flags=re.DOTALL | re.IGNORECASE,
    )
    assert blocks, f"No JSON-LD found in {path.relative_to(ROOT)}"
    return [json.loads(block) for block in blocks]


def test_offer_has_one_audience_price_and_checkout_destination() -> None:
    page = _text(OFFER)
    assert "Ontario businesses with 10–250 staff" in page
    assert "Microsoft 365" in page
    assert "CAD $249" in page
    checkout_urls = re.findall(r'href="(https://buy\.stripe\.com/[^"]+)"', page)
    assert checkout_urls
    assert set(checkout_urls) == {STRIPE_URL}
    assert 'data-cg-event="begin_checkout"' in page
    assert 'data-cg-offer="quick-audit"' in page
    assert 'data-cg-value="249"' in page
    assert "REPLACE_QUICKAUDIT" not in page


def test_offer_is_authorization_gated_and_routes_a_crm_ready_lead() -> None:
    page = _text(OFFER)
    assert "Written scope and authorization first" in page
    assert "read-only" in page.lower()
    assert 'data-cg-lead-form' in page
    assert 'name="pipeline_stage" value="New qualified lead"' in page
    assert 'name="lead_value_cad" value="249"' in page
    assert "/assets/js/lead-pipeline.js" in page
    assert "Do not include passwords, secrets" in page
    pipeline = _text(ROOT / "operations" / "quick-audit-crm-pipeline.md")
    assert "Payment verified" in pipeline
    assert "Neither proves a\n  successful payment" in pipeline


def test_sample_report_cannot_be_mistaken_for_customer_evidence() -> None:
    page = _text(SAMPLE)
    assert "Synthetic demonstration — not a client report" in page
    assert "fictional" in page.lower()
    assert "maple-north.example" in page
    assert "No real organization, tenant, scan, client evidence or customer result" in page
    assert "QA-01" in page and "QA-04" in page
    _json_ld(SAMPLE)


def test_methodology_publishes_scoring_limits_and_primary_sources() -> None:
    page = _text(METHOD)
    assert "Risk score = likelihood × impact" in page
    assert "Missing evidence is marked “not verified”" in page
    assert "No guarantee that every vulnerability" in page
    for url in (
        "https://www.cyber.gc.ca/en/guidance/baseline-cyber-security-controls-small-and-medium-organizations",
        "https://www.nist.gov/publications/nist-cybersecurity-framework-csf-20",
        "https://learn.microsoft.com/en-us/microsoft-365/admin/security-and-compliance/set-up-multi-factor-authentication?view=o365-worldwide",
        "https://learn.microsoft.com/en-us/entra/identity/conditional-access/managed-policies",
        "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
    ):
        assert url in page
    _json_ld(METHOD)


def test_checkout_return_is_measured_but_never_claimed_as_purchase() -> None:
    page = _text(THANKS)
    assert 'window.cgTrack("checkout_return"' in page
    assert "this page does not prove that a Stripe payment succeeded" in page
    assert 'window.cgTrack("purchase"' not in page
    assert "Stripe dashboard or a verified Stripe webhook" in _text(ROOT / "offers" / "README.md")


def test_search_console_verification_is_retained() -> None:
    verification_file = ROOT / f"google{SEARCH_CONSOLE_TOKEN}.html"
    assert verification_file.exists()
    assert SEARCH_CONSOLE_TOKEN in _text(verification_file)
    home = _text(ROOT / "index.html")
    assert f'<meta name="google-site-verification" content="{SEARCH_CONSOLE_TOKEN}"' in home
    assert "https://www.clearglassinc.com/offers/security-quick-audit-methodology.html" in _text(ROOT / "sitemap.xml")
    assert "https://www.clearglassinc.com/offers/security-quick-audit-sample-report.html" in _text(ROOT / "sitemap.xml")


def test_offer_structured_data_is_valid_json() -> None:
    graph = _json_ld(OFFER)[0]["@graph"]
    service = next(node for node in graph if node.get("@type") == "Service")
    assert service["offers"]["price"] == "249"
    assert service["offers"]["priceCurrency"] == "CAD"
    assert service["offers"]["url"] == STRIPE_URL
