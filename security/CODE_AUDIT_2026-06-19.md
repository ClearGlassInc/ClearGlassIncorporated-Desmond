# Code Security Audit — 2026-06-19

Scope: `ClearGlassInc/ClearGlassInc.github.io` (Python agent/bot layer + static site).
Tools: `bandit` (SAST), `pip-audit` (dependency CVEs), `ruff` (lint), `pytest`
(253 + 152 sentinel tests). Baseline: **0 high**, 13 medium, 739 low bandit
findings; **0** dependency vulnerabilities.

## Summary

| Area | Result |
|------|--------|
| Dependency vulnerabilities (`pip-audit`) | ✅ none |
| High-severity SAST | ✅ none |
| Tests | ✅ 253 repo + 152 sentinel passing |
| Lint (`ruff`) | ✅ clean |

## Fixed

### 1. Untrusted external XML parsing — `sentinel/sentinel/collector.py` (B314)
`parse_feed()` parses **untrusted external RSS/Atom feeds**, so a hostile feed
could attempt an entity-expansion ("billion laughs") attack. Hardened by parsing
through `defusedxml` when available, with a safe stdlib fallback (Python's
`ElementTree` has no external-entity resolver, so XXE file reads are not
possible). Malicious feeds now fail closed as `CollectorError`.
- Added `defusedxml>=0.7` as an optional hardening dependency in
  `sentinel/requirements.txt` (the pure-stdlib trust loop still runs without it).
- Verified: with `defusedxml` installed, an entity-bomb feed is rejected; without
  it, all 152 sentinel tests still pass.

### 2. URL scheme allowlist — `scripts/control_surface_feeds.py` `probe()` (B310)
`probe(url)` accepts a free-form URL. Added a scheme allowlist
(`http`/`https` only) so a misconfigured or attacker-supplied target cannot turn
the health probe into a `file://`/`ftp://` read (CWE-22 / SSRF).

## Reviewed and accepted (no change)

| Finding | Location(s) | Rationale |
|---------|-------------|-----------|
| B310 urlopen | `bots/alert_dispatcher_bot.py`, `bots/site_health_bot.py`, `scripts/{repo_audit,api_security_scanner,access_control_audit,control_surface_feeds(gh_api)}.py`, `automation/v0.2/clearglass_agent_runtime.py` | URLs are built from **hardcoded/trusted bases** (GitHub API, the project's own `https://clearglassinc.github.io`), not attacker input. No SSRF path. |
| B318/B314 XML | `scripts/osint_deck_release.py`, `scripts/site_reliability_audit.py` | Parse the repo's **own committed `sitemap.xml`** (trusted, generated in-repo). These scripts run in CI with stdlib only; adding a dependency would expand CI blast radius for no real-world gain. |
| B104 bind 0.0.0.0 | `clearglass-commerce/control-plane/app/main.py` | Intentional for a containerized service listening on all interfaces. |
| B105 "hardcoded password" | various | False positives — string literals `"PASS"`, `"FAIL"`, `"tok"` are status/label values, not credentials. |
| B101 assert (716) | `tests/**` | Asserts in test code; expected. |

## Verification

```
pytest tests/        -> 253 passed
pytest sentinel/tests -> 152 passed
ruff check .         -> all checks passed
pip-audit            -> no known vulnerabilities
bandit -r .          -> 0 high, 0 unaccepted medium
```
