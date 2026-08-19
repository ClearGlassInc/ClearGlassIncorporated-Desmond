#!/usr/bin/env bash
#
# Local equivalent of the `Agent SDK CI` workflow.
#
# Use this when GitHub Actions can't verify a change — during a runner outage,
# an Actions billing stop, or simply to get the same answer without pushing.
# It runs the workflow's exact steps in a throwaway virtualenv per Python
# version, then validates the substance of the container build.
#
#   ./scripts/verify.sh                 # every interpreter found, plus container checks
#   ./scripts/verify.sh 3.11 3.12       # only these interpreters
#   SKIP_CONTAINER=1 ./scripts/verify.sh
#
# Exit status is 0 only if every leg passed, so it is safe to gate on.
set -u

SDK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKDIR="${TMPDIR:-/tmp}/cg-verify-$$"
PORT="${VERIFY_PORT:-8099}"
FAILURES=()

cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
pass() { printf '  \033[32mPASS\033[0m  %s\n' "$*"; }
fail() { printf '  \033[31mFAIL\033[0m  %s\n' "$*"; FAILURES+=("$1"); }

# --- Which interpreters to test -------------------------------------------
if [ "$#" -gt 0 ]; then
  VERSIONS=("$@")
else
  VERSIONS=()
  for v in 3.10 3.11 3.12 3.13; do
    command -v "python$v" >/dev/null 2>&1 && VERSIONS+=("$v")
  done
fi

if [ "${#VERSIONS[@]}" -eq 0 ]; then
  echo "No supported python interpreter found (need 3.10+)." >&2
  exit 1
fi

# --- Job 1: lint + test matrix --------------------------------------------
for v in "${VERSIONS[@]}"; do
  PYBIN="python$v"
  log "Lint and test (py$v)"

  if ! command -v "$PYBIN" >/dev/null 2>&1; then
    fail "py$v: interpreter not found"; continue
  fi

  VENV="$WORKDIR/venv-$v"
  if ! "$PYBIN" -m venv "$VENV" >/dev/null 2>&1; then
    fail "py$v: venv creation"; continue
  fi

  # `all` is included so the provider-adapter tests run rather than skip.
  if ! (cd "$SDK_DIR" && "$VENV/bin/pip" install -q --upgrade pip >/dev/null 2>&1 \
        && "$VENV/bin/pip" install -q -e ".[dev,server,all]" >/dev/null 2>&1); then
    fail "py$v: install"; continue
  fi
  pass "py$v: install"

  if (cd "$SDK_DIR" && "$VENV/bin/ruff" check .) >/dev/null 2>&1; then
    pass "py$v: ruff"
  else
    fail "py$v: ruff"
    (cd "$SDK_DIR" && "$VENV/bin/ruff" check .) 2>&1 | tail -20
  fi

  if (cd "$SDK_DIR" && "$VENV/bin/python" -m pytest -q) >"$WORKDIR/pytest-$v.log" 2>&1; then
    pass "py$v: pytest — $(grep -Eo '[0-9]+ passed[^=]*' "$WORKDIR/pytest-$v.log" | tail -1 | tr -d '\n')"
  else
    fail "py$v: pytest"
    tail -25 "$WORKDIR/pytest-$v.log"
  fi

  EX_OK=1
  for ex in examples/hello_agent.py examples/streaming_agent.py examples/advanced_agent.py; do
    (cd "$SDK_DIR" && "$VENV/bin/python" "$ex") >/dev/null 2>&1 || { EX_OK=0; echo "      $ex failed"; }
  done
  (cd "$SDK_DIR" && "$VENV/bin/python" -m clearglassinc_sdk.cli version) >/dev/null 2>&1 || EX_OK=0
  [ "$EX_OK" -eq 1 ] && pass "py$v: examples + CLI" || fail "py$v: examples + CLI"
done

# --- Job 2: container ------------------------------------------------------
if [ "${SKIP_CONTAINER:-0}" = "1" ]; then
  log "Container checks skipped (SKIP_CONTAINER=1)"
elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  log "Build container (real docker build)"
  if docker build -q -t clearglassinc-sdk:verify "$SDK_DIR" >/dev/null 2>&1; then
    pass "docker build"
    CID=$(docker run -d -p "$PORT:8000" clearglassinc-sdk:verify 2>/dev/null)
    OK=0
    for _ in $(seq 1 20); do
      curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && { OK=1; break; }
      sleep 3
    done
    [ "$OK" -eq 1 ] && pass "container /health" || { fail "container /health"; docker logs "$CID" 2>&1 | tail -20; }
    docker rm -f "$CID" >/dev/null 2>&1
  else
    fail "docker build"
  fi
else
  # No usable daemon: exercise what the Dockerfile actually does instead —
  # wheel build, offline install, then the image's own healthcheck probe.
  log "Dockerfile substance (no docker daemon available)"
  PYBIN="python${VERSIONS[0]}"
  WHEELS="$WORKDIR/wheels"
  RUNTIME="$WORKDIR/runtime"

  "$PYBIN" -m venv "$WORKDIR/builder" >/dev/null 2>&1
  if "$WORKDIR/builder/bin/pip" wheel -q --wheel-dir "$WHEELS" "$SDK_DIR[server,all]" >/dev/null 2>&1; then
    pass "builder stage: pip wheel ($(find "$WHEELS" -name '*.whl' | wc -l | tr -d ' ') wheels)"
  else
    fail "builder stage: pip wheel"
  fi

  "$PYBIN" -m venv "$RUNTIME" >/dev/null 2>&1
  if "$RUNTIME/bin/pip" install -q --no-index --find-links="$WHEELS" "clearglassinc-sdk[server,all]" >/dev/null 2>&1; then
    pass "runtime stage: offline install"
  else
    fail "runtime stage: offline install"
  fi

  CLEARGLASS_SESSION_DIR="$WORKDIR/sessions" PORT="$PORT" \
    "$RUNTIME/bin/python" -m clearglassinc_sdk.server >"$WORKDIR/server.log" 2>&1 &
  SRV=$!
  for _ in $(seq 1 25); do
    curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break
    sleep 1
  done
  # The literal HEALTHCHECK command baked into the image.
  if "$RUNTIME/bin/python" -c \
      "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:$PORT/health', timeout=4).status==200 else 1)" 2>/dev/null; then
    pass "image HEALTHCHECK probe"
  else
    fail "image HEALTHCHECK probe"; tail -20 "$WORKDIR/server.log"
  fi
  kill "$SRV" 2>/dev/null; wait "$SRV" 2>/dev/null
fi

# --- Verdict ---------------------------------------------------------------
echo
if [ "${#FAILURES[@]}" -eq 0 ]; then
  printf '\033[32mALL CHECKS PASSED\033[0m\n'
  exit 0
fi
printf '\033[31m%d CHECK(S) FAILED:\033[0m\n' "${#FAILURES[@]}"
printf '  - %s\n' "${FAILURES[@]}"
exit 1
