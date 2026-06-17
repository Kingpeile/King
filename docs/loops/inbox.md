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

- [ ] **#3 · 8 个 open PR 待盘点去留**（本轮发现源漏看了，由评估器补上）
  open PR：#1 #3 #4 #5 #7 #8 #9 #12。值得先看的：
  - **#8** 昨天（06-16）还在更新，是活的。
  - **#7 / #12** 内容重叠（都在给 CLAUDE.md 加 Karpathy 编码原则），疑似重复。
  - 多数 PR 的 base 不是默认分支而是 `claude/add-claude-documentation-2QQ1A` —— 确认下默认分支与这些长期开着的 PR 该合还是该关。
