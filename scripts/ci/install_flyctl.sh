#!/usr/bin/env bash
set -euo pipefail

version="${FLYCTL_VERSION:-REPLACE_ME}"
if [ -z "$version" ] || [ "$version" = "REPLACE_ME" ] || [ "$version" = "latest" ]; then
  echo "ERROR: FLYCTL_VERSION must be an explicitly approved version in the deploy context; 'latest' is not permitted." >&2
  exit 2
fi

if command -v flyctl >/dev/null 2>&1; then
  actual="$(flyctl version 2>&1)"
  case "$actual" in
    *"$version"*) printf 'flyctl_version=%s\n' "$version"; exit 0 ;;
    *) echo "ERROR: preinstalled flyctl does not match FLYCTL_VERSION." >&2; exit 2 ;;
  esac
fi

installer="$(mktemp)"
trap 'rm -f "$installer"' EXIT

curl --fail --silent --show-error --location \
  --proto '=https' --tlsv1.2 \
  https://fly.io/install.sh \
  -o "$installer"

sh "$installer" "$version"
actual="$("$HOME/.fly/bin/flyctl" version 2>&1)"
case "$actual" in
  *"$version"*)
    printf 'flyctl_version=%s\n' "$version"
    ;;
  *)
    echo "ERROR: installed flyctl version did not match requested version." >&2
    exit 2
    ;;
esac
