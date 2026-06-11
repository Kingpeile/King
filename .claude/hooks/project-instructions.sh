#!/bin/bash
# UserPromptSubmit hook: inject project instructions into context on every prompt.
# This mirrors the "Set project instructions" feature from claude.ai web Projects —
# stdout from a UserPromptSubmit hook is appended to the model's context.
set -euo pipefail

cat <<'EOF'
Think step by step and show reasoning for complex problems. Use specific examples.
EOF
