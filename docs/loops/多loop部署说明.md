# 多 loop 部署说明（本地 launchd）

你已经有一个跑通的周报 loop。再加新 loop（收集箱、健康…）时，**不用每个都写一遍 runner**——
用通用 `loop-runner.sh`,新 loop 只需要：①一个命令文件 ②一个 plist。

> 所有 loop 都在你本地 Mac 上跑（数据在本地）。电脑醒着、到点就跑。

---

## 一次性：装通用 runner

把 `docs/loops/loop-runner.sh` 放到本地 `~/.claude/loop-runner.sh` 并加可执行权限。
（内容见该文件；用 Sonnet、跳过权限、失败自动重试 3 次。）

```bash
chmod +x ~/.claude/loop-runner.sh
```

## 每个新 loop：两步

### 1. 命令文件
把 loop 的命令文件放进 vault 的 `.claude/commands/`(收集箱.md、健康.md 已备好）。

### 2. 一个 plist（定时器）
在 `~/Library/LaunchAgents/` 建一个，照下面模板改三处：
- `Label`(唯一名)
- `ProgramArguments` 里的**命令文件路径**和**日志名**
- `StartCalendarInterval` 的星期/时间（和别的 loop 错开，别同一分钟挤一起）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>            <string>com.king.shoujixiang</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>/Users/king/.claude/loop-runner.sh</string>
    <string>.claude/commands/收集箱.md</string>   <!-- 命令文件 -->
    <string>shoujixiang</string>                    <!-- 日志名 → ~/.claude/shoujixiang.log -->
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key> <integer>1</integer>   <!-- 1=周一 … 0/7=周日 -->
    <key>Hour</key>    <integer>9</integer>
    <key>Minute</key>  <integer>30</integer>
  </dict>
  <key>RunAtLoad</key> <false/>
</dict>
</plist>
```

加载：
```bash
launchctl unload ~/Library/LaunchAgents/com.king.shoujixiang.plist 2>/dev/null
launchctl load   ~/Library/LaunchAgents/com.king.shoujixiang.plist
```

---

## 建议的排期（互相错开，别挤同一时刻）

| loop | 命令文件 | 日志名 | 建议时间 |
|---|---|---|---|
| 周报 | `.claude/commands/周总结.md` | zhouzongzhe | 周三 09:00（已在跑）|
| 收集箱 | `.claude/commands/收集箱.md` | shoujixiang | 周一 09:30 |
| 健康 | `.claude/commands/健康.md` | jiankang | 周日 10:00 |

## 运维（任意 loop 通用）

```bash
# 手动立刻跑一次（部署后先这样验一次）
bash ~/.claude/loop-runner.sh ".claude/commands/收集箱.md" shoujixiang ; tail -20 ~/.claude/shoujixiang.log

# 看某个 loop 在不在岗
launchctl list | grep king

# 停用某个 loop
launchctl unload ~/Library/LaunchAgents/com.king.<名字>.plist
```

## 排错（和周报同款）

- **`idle timeout` / 反复失败** → 代理掐了长连接。换稳定（住宅/家宽）节点；runner 已自带重试 3 次。
- **卡住没输出** → 输出全进日志，屏幕本来就空。开新标签 `tail -f ~/.claude/<日志名>.log` 看实时。
- **想确认定时真触发了** → 到点过后看日志里有没有那个时间戳的 `===== 开始 =====`。
