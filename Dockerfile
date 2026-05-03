# ClearGlassInc — Self-Hosted GitHub Actions Runner Image
# Base: Ubuntu 22.04 LTS
# Stack: Node.js 20, Python 3.11, C++, Docker-in-Docker, cybersecurity tools
FROM ubuntu:22.04

ARG RUNNER_VERSION=2.315.0
ARG DEBIAN_FRONTEND=noninteractive

# ── System packages ───────────────────────────────────────────────────────────
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    curl wget git unzip jq ca-certificates gnupg lsb-release sudo \
    build-essential cmake pkg-config libssl-dev libffi-dev \
    python3.11 python3.11-venv python3-pip \
    nmap netcat-openbsd iproute2 dnsutils \
    libicu70 \
  && rm -rf /var/lib/apt/lists/*

# ── Node.js 20 ────────────────────────────────────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && npm install -g npm@latest \
  && rm -rf /var/lib/apt/lists/*

# ── Python tools ──────────────────────────────────────────────────────────────
RUN pip3 install --no-cache-dir pytest pytest-cov bandit semgrep requests

# ── Docker CLI (Docker-in-Docker via host socket mount) ───────────────────────
RUN install -m 0755 -d /etc/apt/keyrings \
  && curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
       | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
  && chmod a+r /etc/apt/keyrings/docker.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
       https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
       > /etc/apt/sources.list.d/docker.list \
  && apt-get update -qq \
  && apt-get install -y --no-install-recommends docker-ce-cli \
  && rm -rf /var/lib/apt/lists/*

# ── nikto (web scanner) ───────────────────────────────────────────────────────
RUN git clone --depth 1 https://github.com/sullo/nikto.git /opt/nikto \
  && ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto \
  && apt-get install -y --no-install-recommends perl \
  && rm -rf /var/lib/apt/lists/*

# ── trufflehog (secret scanner) ───────────────────────────────────────────────
RUN curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh \
    | sh -s -- -b /usr/local/bin

# ── OWASP Dependency-Check ────────────────────────────────────────────────────
ARG DC_VERSION=9.0.9
RUN curl -fsSL "https://github.com/jeremylong/DependencyCheck/releases/download/v${DC_VERSION}/dependency-check-${DC_VERSION}-release.zip" \
      -o /tmp/dc.zip \
  && unzip -q /tmp/dc.zip -d /opt/ \
  && ln -s /opt/dependency-check/bin/dependency-check.sh /usr/local/bin/dependency-check \
  && rm /tmp/dc.zip

# ── Non-root runner user ──────────────────────────────────────────────────────
RUN useradd -m -s /bin/bash runner \
  && echo "runner ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/runner \
  && chmod 440 /etc/sudoers.d/runner \
  && usermod -aG docker runner 2>/dev/null || true

USER runner
WORKDIR /home/runner

# ── GitHub Actions runner binary ──────────────────────────────────────────────
RUN mkdir actions-runner && cd actions-runner \
  && curl -fsSL -o runner.tar.gz \
       "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" \
  && tar xzf runner.tar.gz \
  && rm runner.tar.gz

# ── Entrypoint: register + run (used for standalone Docker deployments) ───────
COPY --chown=runner:runner infra/docker-entrypoint.sh /home/runner/entrypoint.sh
RUN chmod +x /home/runner/entrypoint.sh

ENTRYPOINT ["/home/runner/entrypoint.sh"]
