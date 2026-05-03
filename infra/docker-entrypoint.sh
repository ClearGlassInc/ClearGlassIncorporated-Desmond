#!/bin/bash
# Entrypoint for standalone Docker-based runner (not used by Terraform/EC2 path).
# Required env vars: GITHUB_TOKEN, RUNNER_NAME (optional), RUNNER_LABELS (optional)
set -euo pipefail

REPO_OR_ORG="${GITHUB_ORG:-ClearGlassInc}"
RUNNER_NAME="${RUNNER_NAME:-clearglass-docker-$(hostname)}"
LABELS="${RUNNER_LABELS:-self-hosted,linux,x64,clearglass,docker}"

REG_URL="https://api.github.com/orgs/${REPO_OR_ORG}/actions/runners/registration-token"

echo "[entrypoint] Fetching registration token..."
TOKEN=$(curl -fsSL -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "$REG_URL" | jq -r '.token')

cd /home/runner/actions-runner

./config.sh \
  --url "https://github.com/${REPO_OR_ORG}" \
  --token "$TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "$LABELS" \
  --unattended \
  --replace

cleanup() {
  echo "[entrypoint] Removing runner registration..."
  ./config.sh remove --token "$TOKEN" || true
}
trap cleanup EXIT INT TERM

echo "[entrypoint] Runner starting..."
./run.sh
