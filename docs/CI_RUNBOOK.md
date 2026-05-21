# ClearGlass Website CI Runbook

## Source of truth

Repository: `ClearGlassInc/ClearGlassInc.github.io`
Workflow: `01 CI`
Branch: `main`

## Correct workflow path

Use the current `01 CI` workflow on `main`. Do not rerun historical failed workflow attempts from older commits.

## Current validation scope

The workflow validates required static site files, optional Python dependencies, optional Python tests, and HTML parsing across the site.

## Manual GitHub path

Actions -> 01 CI -> Run workflow -> Branch: main -> Run workflow

## Expected result

The latest run should execute against the current `main` branch and validate the modernized website workflow.
