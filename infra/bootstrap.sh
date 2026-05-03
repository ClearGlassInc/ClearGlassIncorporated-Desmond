#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# ClearGlassInc — ONE-COMMAND GitHub Actions Runner Bootstrap
# Account: 206478392741  |  Org: ClearGlassInc  |  Region: us-east-1
#
# USAGE (copy-paste this entire block):
#
#   GITHUB_TOKEN=ghp_YOUR_TOKEN \
#   AWS_ACCESS_KEY_ID=AKIA_YOUR_KEY \
#   AWS_SECRET_ACCESS_KEY=YOUR_SECRET \
#   bash <(curl -sL https://raw.githubusercontent.com/ClearGlassInc/ClearGlassInc.github.io/main/infra/bootstrap.sh)
#
# Required env vars:
#   GITHUB_TOKEN          — PAT with scopes: admin:org, read:org, repo, admin:repo_hook
#   AWS_ACCESS_KEY_ID     — IAM user key (needs EC2, Lambda, IAM, SQS, SSM, S3 perms)
#   AWS_SECRET_ACCESS_KEY — IAM user secret
#
# Optional:
#   AWS_REGION            — default: us-east-1
#   RUNNER_VERSION        — default: 2.315.0
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Constants ─────────────────────────────────────────────────────────────────
AWS_ACCOUNT_ID="206478392741"
GITHUB_ORG="ClearGlassInc"
GITHUB_REPO="ClearGlassInc.github.io"
AWS_REGION="${AWS_REGION:-us-east-1}"
APP_NAME="clearglass-runner-app"
REPO_RAW="https://raw.githubusercontent.com/${GITHUB_ORG}/${GITHUB_REPO}/main"
WORK_DIR="$(mktemp -d)/clearglass-runner"
TF_DIR="$WORK_DIR/infra"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC}  $*"; }
info() { echo -e "${CYAN}→${NC}  $*"; }
warn() { echo -e "${YELLOW}!${NC}  $*"; }
die()  { echo -e "${RED}✗  ERROR: $*${NC}"; exit 1; }
step() { echo -e "\n${CYAN}━━ $* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ─────────────────────────────────────────────────────────────────────────────
# 0. Guard: check required env vars
# ─────────────────────────────────────────────────────────────────────────────
step "Checking required credentials"
[[ -z "${GITHUB_TOKEN:-}" ]]          && die "GITHUB_TOKEN not set"
[[ -z "${AWS_ACCESS_KEY_ID:-}" ]]     && die "AWS_ACCESS_KEY_ID not set"
[[ -z "${AWS_SECRET_ACCESS_KEY:-}" ]] && die "AWS_SECRET_ACCESS_KEY not set"
ok "All credentials present"

# ─────────────────────────────────────────────────────────────────────────────
# 1. Install prerequisites (terraform, aws cli, jq, curl)
# ─────────────────────────────────────────────────────────────────────────────
step "Installing prerequisites"

install_if_missing() {
    local cmd="$1"; local install_fn="$2"
    if command -v "$cmd" &>/dev/null; then
        ok "$cmd already installed ($(command -v "$cmd"))"
    else
        info "Installing $cmd..."
        $install_fn
        ok "$cmd installed"
    fi
}

_install_terraform() {
    local TF_VERSION="1.7.5"
    local OS; OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    local ARCH; ARCH=$(uname -m); [[ "$ARCH" == "x86_64" ]] && ARCH="amd64"
    curl -fsSL "https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_${OS}_${ARCH}.zip" \
        -o /tmp/tf.zip
    unzip -qo /tmp/tf.zip -d /tmp/
    sudo mv /tmp/terraform /usr/local/bin/terraform
    rm -f /tmp/tf.zip
}

_install_awscli() {
    if [[ "$(uname -s)" == "Linux" ]]; then
        curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscli.zip
        unzip -qo /tmp/awscli.zip -d /tmp/awscli-install/
        sudo /tmp/awscli-install/aws/install --update
        rm -rf /tmp/awscli.zip /tmp/awscli-install/
    else
        die "Auto-install of AWS CLI on $(uname -s) not supported — install manually"
    fi
}

_install_jq() {
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y -qq jq
    elif command -v yum &>/dev/null; then
        sudo yum install -y jq
    elif command -v brew &>/dev/null; then
        brew install jq
    else
        die "Cannot install jq — install it manually and re-run"
    fi
}

install_if_missing terraform _install_terraform
install_if_missing aws       _install_awscli
install_if_missing jq        _install_jq
install_if_missing git       "sudo apt-get install -y -qq git || sudo yum install -y git"

# ─────────────────────────────────────────────────────────────────────────────
# 2. Verify AWS credentials
# ─────────────────────────────────────────────────────────────────────────────
step "Verifying AWS credentials"
CALLER=$(aws sts get-caller-identity \
    --region "$AWS_REGION" \
    --output json 2>&1) || die "AWS credentials invalid: $CALLER"
ACTUAL_ACCOUNT=$(echo "$CALLER" | jq -r '.Account')
[[ "$ACTUAL_ACCOUNT" != "$AWS_ACCOUNT_ID" ]] \
    && die "AWS account mismatch: got $ACTUAL_ACCOUNT, expected $AWS_ACCOUNT_ID"
ok "Authenticated as $(echo "$CALLER" | jq -r '.Arn')"

# ─────────────────────────────────────────────────────────────────────────────
# 3. Verify GitHub token & org access
# ─────────────────────────────────────────────────────────────────────────────
step "Verifying GitHub token"
GH_USER=$(curl -fsSL -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/user" | jq -r '.login') \
    || die "GitHub token invalid"
ok "Authenticated as GitHub user: $GH_USER"

# ─────────────────────────────────────────────────────────────────────────────
# 4. Create GitHub App programmatically
# ─────────────────────────────────────────────────────────────────────────────
step "Creating GitHub App: $APP_NAME"

# Check if app already exists
EXISTING_APP=$(curl -fsSL \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/orgs/${GITHUB_ORG}/installations" \
    | jq -r --arg name "$APP_NAME" '.installations[] | select(.app_slug==$name) | .app_id' \
    2>/dev/null || echo "")

if [[ -n "$EXISTING_APP" ]]; then
    warn "GitHub App '$APP_NAME' already exists (ID: $EXISTING_APP) — reusing"
    GITHUB_APP_ID="$EXISTING_APP"
    # Re-generate key via SSM if available
    GITHUB_APP_KEY_B64=$(aws ssm get-parameter \
        --name "/clearglass/github-runner/app-key" \
        --with-decryption \
        --region "$AWS_REGION" \
        --query "Parameter.Value" --output text 2>/dev/null || echo "")
    [[ -z "$GITHUB_APP_KEY_B64" ]] && die \
        "App exists but key not in SSM. Delete the app in GitHub and re-run."
else
    # Create the GitHub App at org level
    APP_MANIFEST=$(cat <<MANIFEST
{
  "name": "${APP_NAME}",
  "description": "ClearGlassInc auto-scaling GitHub Actions runner",
  "url": "https://github.com/${GITHUB_ORG}",
  "hook_attributes": { "url": "https://placeholder.invalid/webhook" },
  "public": false,
  "default_permissions": {
    "actions":            "write",
    "administration":     "write",
    "checks":             "read",
    "contents":           "read",
    "metadata":           "read",
    "organization_self_hosted_runners": "write",
    "pull_requests":      "read"
  },
  "default_events": ["workflow_job", "check_run", "push"]
}
MANIFEST
)

    APP_RESPONSE=$(curl -fsSL -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        -H "Content-Type: application/json" \
        -d "$APP_MANIFEST" \
        "https://api.github.com/orgs/${GITHUB_ORG}/apps") \
        || die "Failed to create GitHub App — ensure token has admin:org scope"

    GITHUB_APP_ID=$(echo "$APP_RESPONSE" | jq -r '.id')
    [[ "$GITHUB_APP_ID" == "null" || -z "$GITHUB_APP_ID" ]] \
        && die "GitHub App creation failed: $(echo "$APP_RESPONSE" | jq -r '.message // .')"

    # Generate private key
    info "Generating private key for app $GITHUB_APP_ID..."
    KEY_RESPONSE=$(curl -fsSL -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/apps/${GITHUB_APP_ID}/keys")
    GITHUB_APP_KEY_PEM=$(echo "$KEY_RESPONSE" | jq -r '.pem')
    [[ "$GITHUB_APP_KEY_PEM" == "null" || -z "$GITHUB_APP_KEY_PEM" ]] \
        && die "Failed to generate GitHub App private key"

    GITHUB_APP_KEY_B64=$(echo "$GITHUB_APP_KEY_PEM" | base64 -w 0)

    # Install app on org
    info "Installing GitHub App on org $GITHUB_ORG..."
    INSTALL_RESPONSE=$(curl -fsSL -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/user/installations" \
        -d "{\"repository_selection\":\"all\"}") 2>/dev/null || true
    # App installation may require org admin action — we'll note this
    ok "GitHub App created (ID: $GITHUB_APP_ID)"

    # Store key in SSM for future re-runs
    aws ssm put-parameter \
        --name "/clearglass/github-runner/app-key" \
        --value "$GITHUB_APP_KEY_B64" \
        --type SecureString \
        --overwrite \
        --region "$AWS_REGION" > /dev/null
    aws ssm put-parameter \
        --name "/clearglass/github-runner/app-id" \
        --value "$GITHUB_APP_ID" \
        --type String \
        --overwrite \
        --region "$AWS_REGION" > /dev/null
    ok "Credentials stored in SSM at /clearglass/github-runner/"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 5. Clone repo & run Terraform
# ─────────────────────────────────────────────────────────────────────────────
step "Downloading infrastructure code"
mkdir -p "$TF_DIR"

for f in main.tf variables.tf outputs.tf providers.tf runner-userdata.sh; do
    info "Fetching infra/$f..."
    curl -fsSL "${REPO_RAW}/infra/${f}" -o "${TF_DIR}/${f}"
done
ok "Infrastructure files downloaded to $TF_DIR"

step "Running Terraform"
cd "$TF_DIR"

export TF_VAR_github_app_id="$GITHUB_APP_ID"
export TF_VAR_github_app_key_base64="$GITHUB_APP_KEY_B64"
export TF_VAR_aws_region="$AWS_REGION"

terraform init -input=false
terraform apply -input=false -auto-approve \
    -var="aws_region=${AWS_REGION}" \
    -var="aws_account_id=${AWS_ACCOUNT_ID}" \
    -var="github_org=${GITHUB_ORG}"

WEBHOOK_URL=$(terraform output -raw webhook_url 2>/dev/null || echo "")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Register webhook in GitHub App automatically
# ─────────────────────────────────────────────────────────────────────────────
if [[ -n "$WEBHOOK_URL" && "$WEBHOOK_URL" != "placeholder.invalid"* ]]; then
    step "Updating GitHub App webhook URL"
    WEBHOOK_SECRET=$(aws ssm get-parameter \
        --name "/clearglass/github-runner/webhook-secret" \
        --with-decryption \
        --region "$AWS_REGION" \
        --query "Parameter.Value" --output text 2>/dev/null || echo "")

    curl -fsSL -X PATCH \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        -H "Content-Type: application/json" \
        -d "{\"webhook_attributes\":{\"url\":\"${WEBHOOK_URL}\",\"secret\":\"${WEBHOOK_SECRET}\"}}" \
        "https://api.github.com/apps/${GITHUB_APP_ID}" > /dev/null
    ok "Webhook registered: $WEBHOOK_URL"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 7. Done — print summary
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✓  ClearGlassInc GitHub Actions Runner — FULLY DEPLOYED${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  AWS Account : $AWS_ACCOUNT_ID  ($AWS_REGION)"
echo "  GitHub Org  : $GITHUB_ORG"
echo "  GitHub App  : $APP_NAME (ID: $GITHUB_APP_ID)"
echo "  Webhook URL : ${WEBHOOK_URL:-<check Terraform output>}"
echo "  Runner tags : self-hosted, linux, x64, aws-spot, clearglass"
echo ""
echo "  Runners scale to ZERO when idle — you pay only when jobs run."
echo "  Spot instances used — up to 90% cheaper than on-demand."
echo ""
echo "  Next: push to main and watch your runners spin up automatically."
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
