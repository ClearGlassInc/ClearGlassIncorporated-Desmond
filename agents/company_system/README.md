# ClearGlassInc Artemis Company Agent System

This directory defines a static-compatible automation architecture for the ClearGlassInc Artemis command system. It does not require a live backend. GitHub Actions, Python validation scripts, JSON registries, and documented prompts coordinate agents safely.

## Operating model

1. Intake classifies work.
2. Planner writes a reversible plan and test gates.
3. Executor changes only approved files.
4. Auditor runs validation for links, assets, workflows, security posture, SEO, accessibility, and deployment readiness.
5. Deployment verifies GitHub Pages artifact creation and emits a summary.
6. Logger records outcome, failures, and next action.
7. Marketing, Revenue, Compliance, and Monitoring agents provide specialized sidecar checks.

See `agent_registry.json` for machine-readable routing.
