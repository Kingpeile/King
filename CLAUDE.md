# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Status

This repository is currently empty. No source files, build configuration, or commits exist yet. Update this file once the project is initialized with its stack, structure, and workflows.

## Agent skills

### Issue tracker

Issues for this repo live on GitHub (Kingpeile/King) and are managed via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical 5-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`); labels are created lazily on first triage. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` at the repo root and `docs/adr/` for architectural decisions (both created lazily by `/grill-with-docs`). See `docs/agents/domain.md`.

## MCP servers

### token-saver

Local hybrid-RAG server over `documents/`. Ask it questions instead of reading
whole files — it returns only the passages that answer the question, each tagged
with a source file and page number. Registered in `.mcp.json`; source and full
docs in `tools/token-saver/README.md`.

- **Use `search_documents` before `read_pages`.** Reading a document whole is
  what this server exists to avoid, and its page citations are checkable.
- Nothing leaves the machine; `documents/` is the only readable folder and is
  gitignored.
- Hybrid (BM25 + local embeddings) locally. Web sessions run keyword-only —
  the embedding weights come from `huggingface.co`, which the cloud network
  policy blocks.

## Session setup (Claude Code on the web)

The cloud container is ephemeral, so a `SessionStart` hook restores user-level skills on every cold session:

- **`.claude/hooks/session-start.sh`** — installs [agentmemory](https://github.com/jayzeng/agentmemory) (persistent cross-session memory CLI), the [mattpocock/skills](https://github.com/mattpocock/skills) pack (14 engineering/productivity skills), and the `token-saver` venv (core/keyword-only). Idempotent: ~2ms when already installed, ~3s cold. Only runs when `CLAUDE_CODE_REMOTE=true`.
- Registered in `.claude/settings.json` under `hooks.SessionStart`.
- The same hook is mirrored at the user level (`~/.claude/hooks/install-skills.sh` + `~/.claude/settings.json`) so other repos / fresh conversations get the same skills automatically. The user-level copy is the primary; this repo-level copy is a safety net in case `~/.claude/` is wiped.

After install, available skills include: `diagnose`, `tdd`, `prototype`, `triage`, `to-issues`, `to-prd`, `grill-me`, `grill-with-docs`, `improve-codebase-architecture`, `handoff`, `write-a-skill`, `caveman`, `zoom-out`, `setup-matt-pocock-skills`, and `agent-memory`. Most are auto-invoked from natural-language intent; `/zoom-out` and `/setup-matt-pocock-skills` must be typed explicitly.
