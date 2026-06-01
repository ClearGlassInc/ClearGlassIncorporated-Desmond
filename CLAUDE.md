# CLAUDE.md — Engineering & DevSecOps Charter

Operating instructions for Claude Code (and any AI agent) working in this
repository. Read this before making changes. It encodes how we build and
maintain **ClearGlassInc Artemis** — the public GitHub Pages site plus its
Python automation — to enterprise, secure-by-design standards.

---

## 1. Mission

Maintain a production website that is **secure by design, automated by
default, and resilient under real use**. Treat every change as if it touches
sensitive systems. Prefer automation for review, testing, scanning,
deployment, and recovery over manual, one-off effort.

## 2. What this repo is

- A **static site** served by GitHub Pages from `main` (`index.html`, product
  pages, `legal/`, `assets/`). No server-side runtime in production; `.nojekyll`
  means HTML is served as-is.
- **Python 3.11 automation** in `bots/` and `scripts/`, exercised by `pytest`
  in `tests/` and run by scheduled GitHub Actions workflows.
- Operative implication: the runtime attack surface is the static site +
  GitHub Actions supply chain, **not** a web backend. Security work focuses on
  CI/CD hygiene, secret protection, dependency/workflow integrity, and safe
  static content — not on app-server hardening that doesn't exist here.

## 3. Operating rules

- Work independently; make sound engineering decisions without seeking
  approval for routine work. Ask only when a missing detail genuinely blocks
  implementation or when a change is hard to reverse / outward-facing.
- Make the **smallest correct change** that accomplishes the goal. No
  speculative abstractions.
- Never leave the repo half-finished. Validate before pushing.
- Return concrete edits, code, and verification steps — not vague advice.
- Match the surrounding code's style, naming, and comment density.

## 4. Branch & commit workflow

- Branch from `main`; `main` is protected and changes land via PR.
- AI-assisted branches: `claude/<scope>-<id>`. Human work: `feature/<scope>`,
  fixes: `fix/<scope>`. Lowercase, hyphen-separated, scoped.
- Commit or push only when asked. **Do not open a PR unless explicitly
  requested.**
- Scheduled bots commit output with `[skip ci]` to avoid feedback loops.

## 5. Security standard (secure-by-design)

- **No secrets in the repo** — ever. API keys, tokens, credentials live in
  GitHub Actions secrets. `.env`, `prompts/`, `secrets/` stay git-ignored.
- Every workflow declares an explicit least-privilege `permissions:` block.
- Pin third-party actions and keep `dependency-review` / secret scanning /
  CodeQL paths green. Treat critical findings as blocking.
- Validate and sanitize any externally-sourced input (issue/PR bodies, CI
  logs, webhook payloads) before acting on it.
- Vulnerability reports go to the contact in `SECURITY.md`. Honor disclosure
  scope and SLAs.

## 6. Automation standard

Codify recurring maintenance as workflows/scripts rather than describing it:
linting, tests, dependency review, secret scanning, YAML/workflow linting,
broken-link and site-integrity checks, sitemap/metadata validation, and
artifact/report generation. If a task can be a script or workflow, implement it.

## 7. Development standard

- Preserve accessibility, performance, and maintainability on the static site:
  semantic HTML, meta/SEO tags, no console errors, optimized assets.
- Python: target 3.11. Financial logic uses `Decimal`, never `float`. Model
  dataclasses are `frozen=True`. No runtime deps beyond the stdlib unless added
  to `requirements.txt`. Don't touch `tests/conftest.py` without clear reason.
- `workflow_dispatch` inputs must mirror every env var the target script reads.
- Test jobs cache pip with `cache: pip`.

## 8. Maintenance standard

Proactively find broken functionality, regressions, outdated deps, security
gaps, and content drift; fix before they become outages. On failure: diagnose
root cause, repair, verify, and note the lesson so it doesn't recur.

## 9. Local validation (run before pushing)

```bash
# Python automation
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install pytest ruff
python -m pytest tests/ -v
ruff check .

# Workflow YAML sanity
python -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('.github/workflows/*.y*ml')]"

# Serve the static site
python3 -m http.server 8000   # http://localhost:8000
```

## 10. CI workflows (source of truth: `.github/workflows/`)

| Workflow | Role |
|---|---|
| `ci.yml` | Python tests, ruff lint, site reliability audit, workflow-doctor dry-run |
| `security.yml` | Dependency review, secret-pattern scan, workflow YAML lint |
| `pages.yml` | GitHub Pages deploy |
| `workflow-doctor.yml` | Workflow health checks |
| `ip-protection-scan.yml` | IP risk: secret/dependency/license scan, AI-authorship & proprietary-notice checks, audit report |

Confirm against the directory listing — workflows change; this table can lag.

## 11. Response format for substantive changes

1. What changed · 2. Why · 3. Files edited/created · 4. The code/config ·
5. Tests / validation run · 6. Security impact · 7. Deploy / maintenance notes.

## 12. Quality bar

Enterprise-grade: secure, stable, fast, auditable. Zero console errors, clean
CI, reliable deploys, no new technical debt or security weakness.
