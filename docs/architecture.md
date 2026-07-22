# ClearGlass Burlington Growth System Architecture

## Repository audit

The repository is a GitHub Pages marketing site with independently deployed backend systems. `CLAUDE.md` identifies the root `*.html`, CSS, JS, and assets as the production static site, with governed commerce systems in `clearglass-commerce/` that must preserve human approval for consequential actions.

## Architecture plan

The growth system is implemented as a deterministic Python control layer (`clearglass_growth/`), static command-centre UI (`apps/command-center/`), YAML configuration, JSON campaign data, agent definitions, workflows, and docs. It does not send messages, publish content, spend ad budget, or collect personal data without approval.

## Controlled workflow

Market signal → opportunity qualification → audience selection → offer selection → campaign brief → content/ad generation → claim verification → compliance review → human approval → publication/export → performance collection → attribution → recommendation → human-approved adjustment.

## Safeguards

All external actions fail closed. Audit logs are hash chained. Public-source research must preserve URLs. Campaign claims require evidence and unsupported claims are rejected.
