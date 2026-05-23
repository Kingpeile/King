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

## Session setup (Claude Code on the web)

The cloud container is ephemeral, so a `SessionStart` hook restores user-level skills on every cold session:

- **`.claude/hooks/session-start.sh`** — installs [agentmemory](https://github.com/jayzeng/agentmemory) (persistent cross-session memory CLI) and the [mattpocock/skills](https://github.com/mattpocock/skills) pack (14 engineering/productivity skills). Idempotent: ~2ms when already installed, ~3s cold. Only runs when `CLAUDE_CODE_REMOTE=true`.
- Registered in `.claude/settings.json` under `hooks.SessionStart`.
- The same hook is mirrored at the user level (`~/.claude/hooks/install-skills.sh` + `~/.claude/settings.json`) so other repos / fresh conversations get the same skills automatically. The user-level copy is the primary; this repo-level copy is a safety net in case `~/.claude/` is wiped.

After install, available skills include: `diagnose`, `tdd`, `prototype`, `triage`, `to-issues`, `to-prd`, `grill-me`, `grill-with-docs`, `improve-codebase-architecture`, `handoff`, `write-a-skill`, `caveman`, `zoom-out`, `setup-matt-pocock-skills`, and `agent-memory`. Most are auto-invoked from natural-language intent; `/zoom-out` and `/setup-matt-pocock-skills` must be typed explicitly.

## Karpathy Coding Guidelines

Behavioral guidelines to reduce common LLM coding mistakes, derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876).

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.
