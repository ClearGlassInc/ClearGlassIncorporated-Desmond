#!/usr/bin/env python3
"""Compare the Stripe account against ClearGlass's own corporate record.

Stripe verifies a business by *keying* the details you typed against government
records. When they disagree it answers `verification_failed_keyed_match` — a
message that names no field, so the usual response is to re-upload the same
document and be rejected again. The mismatch is almost never the document; it is
a character in a field.

This tool finds the field. It reads the corporate facts ClearGlass already
publishes in `legal/articles.html` and diffs them against the Stripe account,
naming the exact API path and the exact difference.

    python3 tools/stripe_account_preflight.py --account-json account.json
    python3 tools/stripe_account_preflight.py            # live, needs STRIPE_SECRET_KEY

Get the account JSON without this tool touching the network:

    curl -s https://api.stripe.com/v1/accounts/acct_XXX -u "$STRIPE_SECRET_KEY:" > account.json

Exit codes: 0 clean · 1 a blocking mismatch · 2 could not read a source.

Read-only. It never writes to Stripe — correcting an account field is a Dashboard
action for the account holder, because it is an assertion about a legal entity.

stdlib only, like the other tools in this directory.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "legal" / "articles.html"

#: Merchant category codes that describe what ClearGlass actually sells:
#: professional/consulting services and computer services. A code from an
#: unrelated trade is a mismatch a reviewer will notice before you do.
PLAUSIBLE_MCC = {
    "7392",  # management, consulting and public relations services
    "7379",  # computer maintenance, repair and services
    "5734",  # computer software stores
    "7372",  # computer programming, data processing
    "8999",  # professional services, not elsewhere classified
}

#: Stems that should appear in a description of what ClearGlass sells. Matched as
#: prefixes so "audit" catches "audits" and "consult" catches "consulting".
EXPECTED_DESCRIPTION_TERMS = {
    "secur", "cyber", "risk", "audit", "consult", "softw", "intellig",
    "workspace", "productiv", "email", "advisor", "threat", "compliance",
}

#: How many DISTINCT stems must appear before a description is accepted.
#:
#: One is not enough, and the reason is concrete: the live account described a
#: trading product as "...built for consistent, risk-managed entries", which
#: shares exactly one stem ("risk") with a cybersecurity business and would sail
#: through a first-match check. Requiring two forces the overlap to be about the
#: subject rather than an incidental adjective.
MIN_DESCRIPTION_TERMS = 2


class PreflightError(RuntimeError):
    """A source could not be read, so no comparison is possible."""


@dataclass
class Finding:
    """One disagreement, with enough detail to act on without guessing."""

    severity: str          # blocking | warning | info
    field_path: str        # the Stripe API path, e.g. company.name
    expected: str
    actual: str
    why: str
    fix: str

    @property
    def blocking(self) -> bool:
        return self.severity == "blocking"


@dataclass
class CorporateRecord:
    """What ClearGlass's own published Articles say about the entity."""

    corporate_name: str | None = None
    corporate_type: str | None = None
    municipality: str | None = None
    province: str | None = None
    country: str | None = None
    incorporator: str | None = None
    status: str | None = None
    draft: bool = False
    notes: list[str] = field(default_factory=list)


def _strip_tags(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def read_corporate_record(path: Path = ARTICLES) -> CorporateRecord:
    """Parse the corporate facts out of the published Articles page.

    The page is the repository's own statement of the entity, so it is the right
    thing to diff Stripe against. It is *not* the government record — see the
    draft flag below, which is surfaced rather than silently trusted.
    """
    if not path.is_file():
        raise PreflightError(f"corporate record not found: {path}")
    text = path.read_text(encoding="utf-8")

    def field_value(label: str) -> str | None:
        match = re.search(rf"<td>{re.escape(label)}</td><td>(.*?)</td>", text, re.S)
        return _strip_tags(match.group(1)) if match else None

    record = CorporateRecord(
        corporate_name=field_value("Corporate Name"),
        corporate_type=field_value("Corporate Type"),
        municipality=field_value("Municipality"),
        province=field_value("Province"),
        country=field_value("Country"),
        incorporator=field_value("Incorporator"),
        status=field_value("Status"),
    )
    if not record.corporate_name:
        raise PreflightError(
            f"{path} has no 'Corporate Name' row — the page layout changed and this "
            "parser is stale. Fix the parser rather than skipping the check."
        )
    # The page labels itself a working draft. That does not make it useless — it
    # is still the intended legal name — but a mismatch against a draft is a
    # question, not a verdict, and the report says so.
    lowered = text.lower()
    record.draft = "working draft" in lowered or "filing not verified" in lowered
    if record.draft:
        record.notes.append(
            "legal/articles.html is labelled a working draft, so it evidences the "
            "INTENDED legal name. The authoritative source is the Certificate of "
            "Incorporation / Ontario Business Registry entry — confirm against that."
        )
    return record


def _normalise(value: str) -> str:
    """Casefold, strip accents and collapse whitespace — nothing else.

    Deliberately does NOT remove punctuation or spaces. "ClearGlassInc" and
    "ClearGlass Inc." must compare as different, because to Stripe's keyed match
    against a registry they *are* different, and hiding that is the whole bug
    this tool exists to catch.
    """
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", without_accents).strip().casefold()


def _squashed(value: str) -> str:
    """Everything alphanumeric, lowercased. Used only to explain a near-miss."""
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _get(account: dict[str, Any], path: str) -> Any:
    node: Any = account
    for part in path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def compare(record: CorporateRecord, account: dict[str, Any]) -> list[Finding]:
    """Diff the account against the corporate record, most severe first."""
    findings: list[Finding] = []
    legal_name = record.corporate_name or ""

    # ── The one that causes verification_failed_keyed_match ────────────────
    for path in ("company.name", "business_profile.name"):
        actual = _get(account, path)
        if actual is None:
            continue
        if _normalise(str(actual)) == _normalise(legal_name):
            continue
        near = _squashed(str(actual)) == _squashed(legal_name)
        findings.append(
            Finding(
                severity="blocking" if path == "company.name" else "warning",
                field_path=path,
                expected=legal_name,
                actual=str(actual),
                why=(
                    "Stripe keys this string against the government record. "
                    + (
                        "The two differ only in spacing or punctuation, which is exactly "
                        "what produces verification_failed_keyed_match — a human reads them "
                        "as the same name and the match algorithm does not."
                        if near
                        else "They are different names."
                    )
                ),
                fix=(
                    f"Set {path} to the registered name exactly as it appears on the "
                    f"Certificate of Incorporation, then re-upload proof of registration."
                ),
            )
        )

    # ── Registered office ──────────────────────────────────────────────────
    address_checks = (
        ("company.address.city", record.municipality, "City of "),
        ("company.address.country", record.country, ""),
    )
    for path, expected, prefix in address_checks:
        if not expected:
            continue
        actual = _get(account, path)
        if actual is None:
            continue
        want = expected[len(prefix):] if prefix and expected.startswith(prefix) else expected
        if path.endswith("country"):
            want = "CA" if _normalise(want) == "canada" else want
        if _normalise(str(actual)) == _normalise(want):
            continue
        findings.append(
            Finding(
                severity="warning",
                field_path=path,
                expected=want,
                actual=str(actual),
                why="The registered office on file should match the Articles.",
                fix=f"Reconcile {path} with the registered office, or correct the Articles.",
            )
        )

    # ── What the account says it sells ─────────────────────────────────────
    description = _get(account, "business_profile.product_description")
    if description:
        words = set(re.findall(r"[a-z]+", str(description).casefold()))
        matched = {stem for stem in EXPECTED_DESCRIPTION_TERMS
                   if any(word.startswith(stem) for word in words)}
        if len(matched) < MIN_DESCRIPTION_TERMS:
            findings.append(
                Finding(
                    severity="blocking",
                    field_path="business_profile.product_description",
                    expected="a description of what this account actually sells",
                    actual=str(description)[:120] + ("…" if len(str(description)) > 120 else ""),
                    why=(
                        f"The description matches only {len(matched)} of the "
                        f"{MIN_DESCRIPTION_TERMS} subject terms needed to look like a "
                        "description of this business. A "
                        "processor comparing the stated product against the live checkout "
                        "pages will read that as a mismatch, and it is a common trigger for "
                        "account review — especially while identity verification is already "
                        "failing."
                    ),
                    fix=(
                        "Update it in the Dashboard to describe the services actually sold. "
                        "There is no API operation for this field."
                    ),
                )
            )

    mcc = _get(account, "business_profile.mcc")
    if mcc and str(mcc) not in PLAUSIBLE_MCC:
        findings.append(
            Finding(
                severity="warning",
                field_path="business_profile.mcc",
                expected="a code describing consulting / computer services",
                actual=str(mcc),
                why="An MCC from an unrelated trade invites review and can affect pricing.",
                fix="Change the category in the Dashboard to match the services sold.",
            )
        )

    # ── Payouts ────────────────────────────────────────────────────────────
    structure = str(_get(account, "company.structure") or "")
    accounts = (_get(account, "external_accounts.data") or [])
    for bank in accounts if isinstance(accounts, list) else []:
        holder = (bank or {}).get("account_holder_name")
        if not holder or "corporation" not in structure:
            continue
        if _squashed(str(holder)) == _squashed(legal_name):
            continue
        findings.append(
            Finding(
                severity="warning",
                field_path="external_accounts.data[].account_holder_name",
                expected=f"{legal_name} (the account is a {structure})",
                actual=str(holder),
                why=(
                    "Payouts from a corporate Stripe account into a personally-named bank "
                    "account are a routine source of payout holds and verification queries."
                ),
                fix="Use a business bank account in the corporation's name, or confirm with the bank that the personal account is registered to the corporation.",
            )
        )

    # ── Outstanding requirements ───────────────────────────────────────────
    due = _get(account, "requirements.currently_due") or []
    for item in due:
        findings.append(
            Finding(
                severity="blocking",
                field_path=f"requirements.currently_due[{item}]",
                expected="satisfied",
                actual="outstanding",
                why="Stripe is waiting on this. Unmet past the deadline, charges stop.",
                fix="Provide it in the Dashboard once the field mismatches above are corrected.",
            )
        )
    for err in _get(account, "requirements.errors") or []:
        findings.append(
            Finding(
                severity="blocking",
                field_path=f"requirements.errors[{(err or {}).get('requirement', '?')}]",
                expected="accepted",
                actual=str((err or {}).get("code", "error")),
                why=str((err or {}).get("reason", "")),
                fix="Correct the mismatched field FIRST, then re-submit. Re-uploading the same document against the same mismatched field fails again.",
            )
        )

    order = {"blocking": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda f: order.get(f.severity, 3))
    return findings


def load_account(path: str | None) -> dict[str, Any]:
    """Read the account from a file, or from the Stripe API when a key is set."""
    if path:
        target = Path(path)
        if not target.is_file():
            raise PreflightError(f"account json not found: {target}")
        return json.loads(target.read_text(encoding="utf-8"))

    key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not key:
        raise PreflightError(
            "no --account-json given and STRIPE_SECRET_KEY is not set.\n"
            "Either export the key, or save the account first:\n"
            '  curl -s https://api.stripe.com/v1/accounts/<acct_id> -u "$STRIPE_SECRET_KEY:" '
            "> account.json"
        )

    import urllib.request  # imported lazily: the file path never touches the network

    account_id = os.environ.get("STRIPE_ACCOUNT_ID", "").strip()
    url = f"https://api.stripe.com/v1/accounts/{account_id}" if account_id else "https://api.stripe.com/v1/account"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed https host
        return json.loads(response.read().decode("utf-8"))


def render(record: CorporateRecord, account: dict[str, Any], findings: list[Finding]) -> str:
    lines: list[str] = []
    acct_id = account.get("id", "(unknown account)")
    lines.append(f"Stripe account preflight — {acct_id}")
    lines.append(f"Corporate record: {record.corporate_name!r} ({ARTICLES.relative_to(ROOT)})")

    deadline = _get(account, "requirements.current_deadline")
    if deadline:
        when = datetime.fromtimestamp(int(deadline), timezone.utc)
        days = (when - datetime.now(timezone.utc)).days
        lines.append(f"Requirements deadline: {when:%Y-%m-%d %H:%M UTC} ({days} days away)")
    lines.append("")

    if not findings:
        lines.append("No mismatches found. Every checked field agrees with the corporate record.")
    for item in findings:
        lines.append(f"[{item.severity.upper()}] {item.field_path}")
        lines.append(f"    expected : {item.expected}")
        lines.append(f"    actual   : {item.actual}")
        if item.why:
            lines.append(f"    why      : {item.why}")
        lines.append(f"    fix      : {item.fix}")
        lines.append("")

    for note in record.notes:
        lines.append(f"NOTE: {note}")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--account-json", help="Path to a saved Stripe account object.")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    args = parser.parse_args(argv)

    try:
        record = read_corporate_record()
        account = load_account(args.account_json)
    except PreflightError as exc:
        print(f"Cannot run: {exc}", file=sys.stderr)
        return 2

    findings = compare(record, account)
    if args.json:
        print(json.dumps([f.__dict__ for f in findings], indent=2))
    else:
        print(render(record, account, findings))
    return 1 if any(f.blocking for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
