#!/usr/bin/env bash
# Install token-saver into a self-contained venv next to this script.
# Idempotent: re-running is a no-op once the venv is present and current.
#
#   ./install.sh          full install (hybrid retrieval)
#   ./install.sh --core   skip the embedding model (keyword-only, ~200MB lighter)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$HERE/.venv"
STAMP="$VENV/.install-stamp"

MODE="full"
if [ "${1:-}" = "--core" ]; then
  MODE="core"
fi

# Bump the version prefix when dependencies change so existing venvs reinstall.
if [ "$MODE" = "core" ]; then
  EXTRAS="pdf-fallback"
  WANT="v1-core"
else
  EXTRAS="pdf-fallback,embeddings,tokens"
  WANT="v1-full"
fi

log() { printf '[token-saver] %s\n' "$*" >&2; }

if [ -f "$STAMP" ] && [ "$(cat "$STAMP")" = "$WANT" ]; then
  log "already installed ($MODE) at $VENV"
  exit 0
fi

if command -v uv >/dev/null 2>&1; then
  uv venv --quiet "$VENV"
  PY="$VENV/bin/python"
  INSTALL=(uv pip install --quiet --python "$PY")
else
  log "uv not found, falling back to python3 -m venv"
  python3 -m venv "$VENV"
  PY="$VENV/bin/python"
  "$PY" -m pip install --quiet --upgrade pip
  INSTALL=("$PY" -m pip install --quiet)
fi

log "installing ($MODE)"
"${INSTALL[@]}" -e "$HERE[pdf-fallback]"

if [ "$MODE" = "full" ]; then
  # fastembed and tiktoken both fetch files on first use and neither is
  # required for the server to run, so a failure here is a warning, not an error.
  "${INSTALL[@]}" -e "$HERE[embeddings,tokens]" \
    || log "WARN: optional extras failed; server will run keyword-only"
fi

"$PY" -c "import token_saver.server" >/dev/null
printf '%s' "$WANT" > "$STAMP"
log "ready: $VENV/bin/token-saver"
