# Loop 配置与成本上限

> 橙皮书 §07：token 爆炸是唯一一笔「冷钱」成本。**上线前先把天花板用数字钉死**，
> 别等账单来教你——一个空转的 bug 能烧掉一整夜的额度。

## 当前上限

| 项 | 值 | 在哪设置 |
|---|---|---|
| 单轮最大轮次 | `--max-turns 30` | `.github/workflows/triage-loop.yml` |
| 调度频率 | 每天一次（cron） | workflow 的 `schedule` |
| 谁能停 | GitHub Actions 超时 / 手动 cancel | Actions 页 |

## 调整建议

- **先小后大**：第一周保持每天一次、max-turns 偏小，观察实际消耗再放宽。
- **加并行前先想清楚预算**：一旦加 worktree 让多个 agent 同时跑，消耗是乘起来的。
- **GitHub Actions 免费额度有限**：私有仓库的 Actions 分钟数会计费，注意 cron 频率。

## 升级路线（什么时候加什么）

| 想要 | 加什么 | checklist 对应项 |
|---|---|---|
| 让它自动起草修复 | triage skill 里放开「act → 开分支改代码」 | 隔离 + 评估器必须先到位 |
| 多个 issue 并行处理 | 给每个 agent 开 `git worktree` | 隔离 |
| 跑到「测试绿」才停 | 引入测试框架 + `/goal` 式停止条件 | 评估器 |
| 自动开 PR / 更新 issue | GitHub MCP connector | 持久化 |

每加一项能力，回到 `README.md` 的 checklist 重新过一遍：**后四项没补齐，就不要放开自动改代码。**
