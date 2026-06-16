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

- **`.claude/hooks/session-start.sh`** — installs [agentmemory](https://github.com/jayzeng/agentmemory) (persistent cross-session memory CLI), the [mattpocock/skills](https://github.com/mattpocock/skills) pack (14 engineering/productivity skills), and [nuwa-skill](https://github.com/alchaincyf/nuwa-skill) (女娲 `huashu-nuwa` — distills a person / thinking style into a runnable persona Skill). It also installs [darwin-skill](https://github.com/alchaincyf/darwin-skill) (alchaincyf/darwin-skill — "Darwin Skill 2.0", an autonomous skill optimizer that scores other skills on a 9-dim rubric, hill-climbs improvements, and keeps-or-reverts based on tests), plus two third-party skill packs (`--all`): [ljg-skills](https://github.com/lijigang/ljg-skills) (李继刚 / 继刚 toolbox, ~22 skills — `ljg-think` 追本之箭/deep-drill, `ljg-read`, `ljg-rank`, `ljg-roundtable`, `ljg-card`, `ljg-paper`, `ljg-book`, …) and [dbskill](https://github.com/dontbesilent2025/dbskill) (dontbesilent business toolbox, ~21 skills — `dbs` main entry/「帮我看看」, `dbs-diagnosis`, `dbs-decision`, `dbs-deconstruct`, `dbs-content`, …). And it mirrors any locally-distilled persona/theme skills committed under `.claude/skills/` (currently `karpathy-perspective`, `gushen`, and `serenity-perspective`) up to the user level so they're globally available (see the `PERSONA_SKILLS` list in the hook). Idempotent: ~2ms when already installed, ~3s cold. Only runs when `CLAUDE_CODE_REMOTE=true`.
- Registered in `.claude/settings.json` under `hooks.SessionStart`.
- The same hook is mirrored at the user level (`~/.claude/hooks/install-skills.sh` + `~/.claude/settings.json`) so other repos / fresh conversations get the same skills automatically. The user-level copy is the primary; this repo-level copy is a safety net in case `~/.claude/` is wiped.

After install, available skills include: `diagnose`, `tdd`, `prototype`, `triage`, `to-issues`, `to-prd`, `grill-me`, `grill-with-docs`, `improve-codebase-architecture`, `handoff`, `write-a-skill`, `caveman`, `zoom-out`, `setup-matt-pocock-skills`, `agent-memory`, `huashu-nuwa`, `darwin-skill`, `karpathy-perspective`, and `gushen`. Most are auto-invoked from natural-language intent; `/zoom-out` and `/setup-matt-pocock-skills` must be typed explicitly. `huashu-nuwa` triggers on phrases like 「造skill」「蒸馏XX」「女娲」「XX的思维方式」. `darwin-skill` is an autonomous skill optimizer (triggers on 「优化skill」「skill打分」「达尔文」「darwin」 etc.) that scores/improves/tests other skills and keeps-or-reverts. `karpathy-perspective` and `gushen` are persona/theme skills distilled by `huashu-nuwa`: `karpathy-perspective` role-plays Andrej Karpathy for AI/ML/software questions (triggers on 「用 Karpathy 的视角」「卡帕西」 etc.); `gushen` is a four-investor advisory board (Buffett / 段永平 / 葛卫东 / Cathie Wood) for investment *thinking*, not buy/sell advice (triggers on 「股神」「巴菲特会怎么看」 etc.); `serenity-perspective` distills Serenity's (@aleabitoreddit) "chokepoint/瓶颈" AI-supply-chain *analysis lens* — finding the irreplaceable bottleneck a king can't live without — framed strictly as analysis-not-buy-signal with heavy honest-boundary warnings (his returns are unverified; independent backtest shows copying him underperformed a sector ETF) (triggers on 「用 Serenity 的视角」「chokepoint」「拆一下这条供应链」 etc.).
