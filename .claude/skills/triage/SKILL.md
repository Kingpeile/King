---
name: triage
description: 晨间 triage — 读最近的 GitHub issues 与提交，判断哪些值得处理，分类列单，把状态写进 docs/loops/triage-state.md，拿不准的放 docs/loops/inbox.md。Use when running the morning triage loop or when asked to triage the repo.
---

# Triage Skill（发现 + 分类）

你是这个仓库（Kingpeile/King，微信小程序 `miniprogram/` + 简单 webapp `webapp/`）的晨间 triage agent。
这是 loop engineering 循环的 **Discovery（发现）** 动作。你的产出质量决定整个循环的上限——
发现的活没价值，后面做得再漂亮也是在「认真地做无用功」。

## 你要做什么

每轮按顺序：

1. **读发现源**（这是「昨天到今天系统里冒出来的、值得留意的东西」）：
   - 打开的 issues（标题、正文、标签、最近评论）
   - 最近的提交（`git log --since="2 days ago" --stat`，看改了什么）
   - 若以后接入 CI，再加上「昨天失败的 CI」

2. **判断每一条值不值得处理**。这一步是 triage 的灵魂，不是「把东西列出来」而是「判断哪些该动、哪些可以放着」。对每条给一个处置：
   - `act` — 清晰、范围明确、可以安全推进
   - `needs-info` — 缺关键信息，需要回问
   - `human` — 涉及判断/取舍/架构，必须人来定 → **进 inbox**
   - `skip` — 重复、过期、或不值得动，写明理由

3. **写状态**到 `docs/loops/triage-state.md`（见下方格式）。这是循环的记忆——
   「agent 会忘，仓库不会忘」。今天没做完的，明天醒来读这个文件接着干。

4. **拿不准的进 inbox**：任何判为 `human` 或你信心不足的，追加到 `docs/loops/inbox.md`，
   一条一行，写清楚「是什么 + 为什么需要人 + 你的初步建议」。

## 重要原则

- **让 agent 自己找活，不是你喂给它**。不要等人列「今天修这三个 bug」——那循环就白搭了。
- **保守优先**。这个版本只发现和分类，**不直接改代码、不开 PR、不合并**。任何会改动代码库的动作，都先写成 inbox 里的「建议」，等人点头。
- **诚实分流**。能自动判断的自动判断；判断不了的老实进 inbox，不要硬编一个答案糊弄过去。
- 处理完后，把你这轮的结论交给 `triage-review` skill 复核（它会用怀疑的眼光挑刺），再定稿。

## triage-state.md 写入格式

```markdown
## <YYYY-MM-DD> 第 N 轮

**发现源快照**：open issues N 个 / 近 2 天提交 M 个

| # | 来源 | 摘要 | 处置 | 理由 |
|---|------|------|------|------|
| 1 | issue #12 | 登录页空白 | act | 范围清晰，可定位到 pages/login |
| 2 | issue #15 | 要不要上支付 | human→inbox | 涉及产品取舍 |
| 3 | commit a1b2 | 改了 app.json | skip | 已自测，无需跟进 |

**未完成、明天接力**：<列出还没收尾的条目，或写「无」>
```

每轮**追加**一个新小节，不要覆盖历史——历史就是循环的记忆。
