# Triage Loop（晨间 triage 循环）

> 一个最小可跑的 loop engineering 骨架。蓝本是《Loop Engineering 橙皮书》§09 与 Addy Osmani 的晨间 triage 循环。
> 核心纪律：**执行可以外包，决策不能。** 这个循环替你做杂活，但每一步都留了一个你能说「不」的口子。

## 它做什么

每天定时自动醒来 → 读最近的 issues 和提交 → 判断哪些值得处理 → 列出清单 → 把拿不准的丢进 inbox 等你 → 把状态写进文件，明天接着干。

它**不会**自动改代码、自动合并。当前版本只做「发现 + 分类 + 评估」，把判断结果摆到你面前。要往「自动起草修复 + 开 PR」扩展时，再按下面的 checklist 补齐隔离与评估闸门。

## 五个动作 → 落在哪个文件

| 动作 | 干什么 | 在这个循环里 |
|---|---|---|
| Discovery 发现 | 自己找出这轮该干的活 | `.claude/skills/triage/SKILL.md` 读 issues + 近期提交 |
| Handoff 交接 | 把任务隔离地交给 agent | （单线程版暂无 worktree；扩展并行时再加） |
| Verification 验证 | 换一个 agent 说「不」 | `.claude/skills/triage-review/SKILL.md`（默认怀疑） |
| Persistence 持久化 | 把状态写到对话之外 | `docs/loops/triage-state.md` + `docs/loops/inbox.md` |
| Scheduling 调度 | 让它自动一轮轮转 | `.github/workflows/triage-loop.yml`（云端，关机也跑） |

## 第一个循环 checklist（橙皮书 §09）

前两项决定**能不能跑**，后四项决定**会不会闯祸**。

- [x] **发现源** — 定时读什么？→ open issues + 近期提交（见 triage skill）
- [x] **状态文件** — 跨轮记忆存哪？→ `docs/loops/triage-state.md`
- [x] **评估器** — 有没有能说「不」的独立检查？→ triage-review skill（独立 agent，默认「假设是坏的」）
- [ ] **隔离** — 每个并行 agent 有自己的 worktree 吗？→ 单线程版暂不需要；并行扩展时补 `-worktree`
- [x] **token 上限** — 设了花费天花板吗？→ workflow 里的 `--max-turns` + 见 `config.md`
- [x] **人工 review 点** — 哪一步暂停让你看？→ `docs/loops/inbox.md`，以及 PR 永远由你审

## 四笔成本，记得守闸（橙皮书 §07）

| 成本 | 一句话防守 |
|---|---|
| 验证债 | 装独立评估器（已有 triage-review），别让干活的自己打分 |
| 理解力衰退 | 每天读一遍 `triage-state.md` 的产出，解释不了就去读代码 |
| 认知投降 | inbox 里的每一条，至少要能说「这个不对」 |
| token 爆炸 | workflow 设了 max-turns；预算/重试上限见 `config.md` |

## 怎么启用

1. 在 GitHub 仓库 Settings → Secrets 配置 `ANTHROPIC_API_KEY`（没有它 workflow 只会空跑）。
2. 确认 `.github/workflows/triage-loop.yml` 里的 cron 时间符合你的时区。
3. 第一次先手动触发（Actions 页 → Run workflow）跑一遍，读 `triage-state.md` 和 `inbox.md` 看产出对不对。
4. 满意了再让它按 schedule 自动转。

## 本地手动跑一轮（不依赖云端）

在 Claude Code 里直接说：

> 用 triage skill 跑一轮，把结果写进 docs/loops/triage-state.md，拿不准的放 docs/loops/inbox.md

或在终端用 `/loop`（需要机器开着）：

```
/loop 1d 用 triage skill 做晨间 triage
```
