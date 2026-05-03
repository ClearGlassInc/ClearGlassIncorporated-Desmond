#!/bin/bash
# Runs on every new EC2 runner at launch — installs the ClearGlassInc toolchain.
# Injected via the philips-labs module's userdata_template mechanism.
set -euo pipefail

yum update -y

# ── Node.js 20 ────────────────────────────────────────────────────────────────
curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -
yum install -y nodejs

# ── Python 3.11 ───────────────────────────────────────────────────────────────
amazon-linux-extras install python3.8 -y 2>/dev/null || true
yum install -y python3 python3-pip
pip3 install --upgrade pip
pip3 install pytest pytest-cov bandit semgrep

# ── C++ build tools ───────────────────────────────────────────────────────────
yum install -y gcc gcc-c++ cmake3 make
ln -sf /usr/bin/cmake3 /usr/bin/cmake 2>/dev/null || true

# ── Docker ────────────────────────────────────────────────────────────────────
yum install -y docker
systemctl enable --now docker
usermod -aG docker ec2-user

# ── Cybersecurity tools ───────────────────────────────────────────────────────
yum install -y nmap git curl wget unzip jq openssl

# nikto (web scanner)
git clone --depth 1 https://github.com/sullo/nikto.git /opt/nikto 2>/dev/null || true
ln -sf /opt/nikto/program/nikto.pl /usr/local/bin/nikto 2>/dev/null || true

# trufflehog (secret scanning)
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh \
  | sh -s -- -b /usr/local/bin 2>/dev/null || true

# OWASP Dependency-Check
DC_VERSION="9.0.9"
curl -fsSL "https://github.com/jeremylong/DependencyCheck/releases/download/v${DC_VERSION}/dependency-check-${DC_VERSION}-release.zip" \
  -o /tmp/dc.zip
unzip -q /tmp/dc.zip -d /opt/
ln -sf /opt/dependency-check/bin/dependency-check.sh /usr/local/bin/dependency-check
rm /tmp/dc.zip

# ── AWS CLI v2 ────────────────────────────────────────────────────────────────
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscli.zip
unzip -q /tmp/awscli.zip -d /tmp/
/tmp/aws/install
rm -rf /tmp/aws /tmp/awscli.zip

echo "[userdata] ClearGlassInc toolchain installed successfully"
