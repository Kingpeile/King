---
name: note-digest
description: 笔记/读书整理循环 — 扫 Obsidian/Inbox 里零散的素材，提炼成结构化卡片存到 Obsidian/Notes，并维护索引与周回顾。原文只读不改。Use when the user says 整理我的笔记 / 做读书卡片 / 笔记周回顾 / digest my notes.
---

# Note Digest Skill（笔记整理循环）

把堆在 `Obsidian/Inbox/`（和 `Obsidian/Daily/`）里的零散素材，提炼成干净、可复用的**卡片**。
这是用户自己的 loop engineering 循环之一，对应五个动作里的**发现 → 生成 → 验证 → 持久化**。

## 铁律：原文只读，绝不改写

`Obsidian/Inbox/` 和 `Obsidian/Daily/` 里的笔记是用户的原始素材，**只读不动、不删不改**。
你的产出一律写到 `Obsidian/Notes/`（整理后的卡片）。原素材保留，方便用户回溯。

## 一轮怎么走

1. **发现**：列出 `Obsidian/Inbox/` 里的笔记，对照 `Obsidian/Notes/_index.md`，
   找出**还没整理成卡片**的。（已整理过的跳过，别重复做工。）

2. **生成卡片**：每条素材产出一张卡片，写到 `Obsidian/Notes/<简短标题>.md`。卡片结构：
   ```markdown
   ---
   title: "<标题>"
   type: card
   tags: [<沿用原 tag + 补充>]
   source: "<原素材文件名>"
   digested: <YYYY-MM-DD>
   ---

   # <标题>

   > **一句话**：<把这条素材浓缩成一句>

   ## 核心观点
   - <3–5 个要点，用你自己的话提炼，但不偏离原意>

   ## 关键澄清 / 易误解处
   - <如果原文有「别误会成 X，其实是 Y」这类，单独拎出来>

   ## 关联
   - <相关的书 / 主题，可用 [[wikilink]] 连到其他卡片>
   ```

3. **验证（轻量 maker-checker）**：卡片写完后，**回到原文核对一遍**——
   有没有曲解原意？有没有把作者没说的话塞进去？标签/归类合不合理？
   发现偏差就改卡片。这一步别省：整理的价值在于忠实浓缩，不是二次创作。

4. **持久化**：更新 `Obsidian/Notes/_index.md`，把新卡片登记进去（标题 + 一句话 + 日期）。

## 周回顾（用户说「笔记周回顾」时）

扫本周新增的素材和卡片，在 `Obsidian/Notes/_index.md` 顶部写一段「本周回顾」：
这周收集了什么主题、有哪些反复出现的关注点、哪些值得深入。不堆流水账，只挑信号。

## 边界

- 不碰 app 代码（`miniprogram/`、`webapp/`），只动 `Obsidian/Notes/`。
- 不确定一条素材该不该整理、或归类拿不准时，问用户，别硬塞。
