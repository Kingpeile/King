# Inbox（等你决定）

> 循环拿不准、或涉及判断/取舍/架构的，都老实放这里等人——这是它「诚实分流」的地方，
> 也是你保持「engineer 而非按钮」的人工 review 点。**这里的每一条，你至少要能说「这个不对」。**
>
> 处理完一条就把它划掉（`- [x]`）或删除。

<!-- triage / triage-review skill 把需要人决定的条目追加到下面，一条一行 -->

### 2026-06-17 第 1 轮

- [ ] **#1 · CLAUDE.md 与现实严重脱节**（comprehension rot 苗头）
  CLAUDE.md 仍写「This repository is currently empty. No source files... no commits exist yet」，
  但实际已有完整的 `miniprogram/` 健康小程序、`webapp/`、`docs/`、loops 骨架、数十个 commit。
  - 建议拆两步：① 事实纠错（删掉 empty / no-commits 断言）—— 范围清晰可逆，**建议直接接受**；
    ② 补一段真实的项目定位与结构描述 —— 涉及「项目该怎么定位」，**由你定**。
  - 我没有自动改 CLAUDE.md：它是根指令文件，影响每个会话，留给你拍板。要我改就说一声。

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
