"""The preflight must catch the mismatch that actually happened.

`verification_failed_keyed_match` names no field, so the failure mode is a loop:
re-upload the document, get rejected, repeat. The test that matters here is the
near-miss one — a name a human reads as identical and a keyed match rejects.
"""
from __future__ import annotations

import json

import pytest

from tools import stripe_account_preflight as preflight


# The shape Stripe returns, with the values that were actually on the live
# account. No secret is involved: this is public business metadata plus an
# account id that already appears in clearglass-commerce/STRIPE_SETUP.md.
def account_fixture(**overrides) -> dict:
    account = {
        "id": "acct_TEST",
        "business_profile": {
            "name": "ClearGlassInc",
            "mcc": "7392",
            "product_description": "Cybersecurity consulting and risk audits for small business.",
        },
        "company": {
            "name": "ClearGlassInc",
            "structure": "private_corporation",
            "address": {"city": "Burlington", "country": "CA", "state": "ON"},
        },
        "external_accounts": {"data": [{"account_holder_name": "ClearGlass Inc."}]},
        "requirements": {"currently_due": [], "errors": []},
    }
    for path, value in overrides.items():
        node = account
        parts = path.split(".")
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = value
    return account


@pytest.fixture()
def record():
    return preflight.read_corporate_record()


# ── The corporate record parses ─────────────────────────────────────────────

def test_reads_the_published_corporate_record(record):
    assert record.corporate_name == "ClearGlass Inc."
    assert record.municipality == "City of Burlington"
    assert record.country == "Canada"


def test_working_draft_status_is_surfaced_not_silently_trusted(record):
    """The Articles page is a draft. A mismatch against it is a question, not a
    verdict, and the report has to say so."""
    assert record.draft is True
    assert any("Certificate of Incorporation" in n for n in record.notes)


# ── The bug that cost a rejected document ───────────────────────────────────

def test_catches_the_spacing_mismatch_that_a_human_reads_as_identical(record):
    """'ClearGlassInc' vs 'ClearGlass Inc.' — the real failure."""
    findings = preflight.compare(record, account_fixture())
    company = [f for f in findings if f.field_path == "company.name"]
    assert company, "the name mismatch was not detected"
    assert company[0].blocking
    assert company[0].actual == "ClearGlassInc"
    assert company[0].expected == "ClearGlass Inc."
    assert "spacing or punctuation" in company[0].why


def test_a_correct_name_produces_no_name_finding(record):
    account = account_fixture(**{"company.name": "ClearGlass Inc.",
                                 "business_profile.name": "ClearGlass Inc."})
    findings = preflight.compare(record, account)
    assert not [f for f in findings if f.field_path.endswith("name")]


def test_normalisation_never_hides_punctuation_or_spacing(record):
    """The whole point. Casefolding is fine; stripping spaces is the bug."""
    assert preflight._normalise("ClearGlass Inc.") != preflight._normalise("ClearGlassInc")
    assert preflight._normalise("clearglass inc.") == preflight._normalise("ClearGlass  Inc.")


@pytest.mark.parametrize("wrong", ["Clearglass Incorporated", "CG Inc.", "Clear Glass Inc."])
def test_catches_outright_different_names(record, wrong):
    findings = preflight.compare(record, account_fixture(**{"company.name": wrong}))
    assert any(f.field_path == "company.name" and f.blocking for f in findings)


# ── The other live-account problems ─────────────────────────────────────────

def test_flags_a_description_that_describes_another_business(record):
    """The live account described trading automation while selling security work."""
    stale = ("Creator of PW Stable Script; a rules-based automation setup built for "
             "consistent, risk-managed entries. DM for details and access.")
    findings = preflight.compare(
        record, account_fixture(**{"business_profile.product_description": stale})
    )
    hit = [f for f in findings if f.field_path == "business_profile.product_description"]
    assert hit and hit[0].blocking
    assert "no API operation" in hit[0].fix


def test_accepts_a_description_that_matches_the_business(record):
    findings = preflight.compare(record, account_fixture())
    assert not [f for f in findings if f.field_path == "business_profile.product_description"]


def test_flags_personal_bank_account_on_a_corporation(record):
    findings = preflight.compare(
        record,
        account_fixture(**{"external_accounts.data": [{"account_holder_name": "Desmond odhiambo"}]}),
    )
    assert any("account_holder_name" in f.field_path for f in findings)


def test_surfaces_outstanding_requirements_and_errors(record):
    account = account_fixture()
    account["requirements"] = {
        "currently_due": ["company.verification.document"],
        "errors": [{
            "code": "verification_failed_keyed_match",
            "reason": "Information on the account doesn't match government records.",
            "requirement": "company.verification.document",
        }],
    }
    findings = preflight.compare(record, account)
    assert any("currently_due" in f.field_path and f.blocking for f in findings)
    err = [f for f in findings if "errors" in f.field_path]
    assert err and "Correct the mismatched field FIRST" in err[0].fix


def test_blocking_findings_sort_first(record):
    account = account_fixture(**{"business_profile.mcc": "5812"})
    findings = preflight.compare(record, account)
    severities = [f.severity for f in findings]
    assert severities == sorted(severities, key=lambda s: {"blocking": 0, "warning": 1}.get(s, 2))


# ── CLI contract ────────────────────────────────────────────────────────────

def test_exit_code_is_nonzero_when_something_blocks(tmp_path, capsys):
    path = tmp_path / "account.json"
    path.write_text(json.dumps(account_fixture()), encoding="utf-8")
    assert preflight.main(["--account-json", str(path)]) == 1
    assert "company.name" in capsys.readouterr().out


def test_exit_code_is_zero_on_a_clean_account(tmp_path, capsys):
    clean = account_fixture(**{"company.name": "ClearGlass Inc.",
                               "business_profile.name": "ClearGlass Inc."})
    path = tmp_path / "account.json"
    path.write_text(json.dumps(clean), encoding="utf-8")
    assert preflight.main(["--account-json", str(path)]) == 0
    assert "No mismatches found" in capsys.readouterr().out


def test_missing_source_exits_two_rather_than_pretending_to_pass(capsys):
    assert preflight.main(["--account-json", "/nonexistent/account.json"]) == 2


def test_never_writes_to_stripe():
    """Correcting a legal-entity field is the account holder's act, not a tool's."""
    source = (preflight.__file__).replace(".pyc", ".py")
    with open(source, encoding="utf-8") as handle:
        text = handle.read()
    for forbidden in ("requests.post", "urlopen(request, data", '"POST"', "method='POST'"):
        assert forbidden not in text, f"preflight must stay read-only ({forbidden})"
