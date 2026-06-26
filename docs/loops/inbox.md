# Inbox（等你决定）

> 循环拿不准、或涉及判断/取舍/架构的，都老实放这里等人——这是它「诚实分流」的地方，
> 也是你保持「engineer 而非按钮」的人工 review 点。**这里的每一条，你至少要能说「这个不对」。**
>
> 处理完一条就把它划掉（`- [x]`）或删除。

<!-- triage / triage-review skill 把需要人决定的条目追加到下面，一条一行 -->

### 2026-06-17 第 1 轮

- [x] **#1 · CLAUDE.md 与现实严重脱节**（comprehension rot 苗头）✅ 2026-06-17 已处理
  原状：CLAUDE.md 写「repository is currently empty... no commits exist yet」，与现实严重不符。
  已重写：补上真实的项目概述（个人健康管理，小程序 + webapp 双端、纯本地存储、无构建/测试）、
  目录结构、约定与坑（含 `cloud/functions/healthData/` 是死代码），并新增 Loops 一节。

- [ ] **#2 · 循环本身的上线闸门未补齐**（needs-info）
  `.github/workflows/triage-loop.yml` 的 cron 已设（每日 UTC 23:00），但：
  ① 仓库 Secrets 里 `ANTHROPIC_API_KEY` 是否已配？没配的话每天会空跑/失败。
  ② workflow 用 `anthropics/claude-code-action@beta`，字段会随版本变，真跑前对照其最新文档校准。
  ③ schedule 只在**默认分支**生效——确认这个 workflow 最终要落到哪个分支。

- [x] **#3 · 8 个 open PR 已盘点**（本轮发现源漏看了，由评估器补上）✅ 2026-06-17 已处理
  用户决策后：
  - **已关闭**：#1（过时文档，CLAUDE.md 已重写）、#4（一次性中文提取脚本）、
    #5（WebGL 能量球 demo）、#7 + #12（重复的编码原则，已并进新版 CLAUDE.md）。
  - **保留（仍开着，待落地）**：#3 记账工具、#8 女娲 skill、#9 东财行情 skill。
- [~] **#3b · 保留的 3 个 PR：按需落地，不急**
  #3 记账 / #8 女娲 / #9 东财，用户说「可能用、还没定」。
  保持 PR 开着即可——代码安全存在各自分支，不会丢。
  哪天确定要用某一个，再把那一个正式并进主线（届时先确认默认分支）。
  目前**无需行动**。
