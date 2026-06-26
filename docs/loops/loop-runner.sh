#!/bin/bash
# ============================================================
# 通用 loop runner —— 跑 vault 里任意一个命令文件（无人值守）
# 用法: loop-runner.sh <命令文件相对vault的路径> <日志名>
# 例:   loop-runner.sh ".claude/commands/收集箱.md" shoujixiang
#       loop-runner.sh ".claude/commands/健康.md"   jiankang
# 所有 loop 共用这一个脚本，新加 loop 只需新建命令文件 + 一个 plist。
# ============================================================

VAULT="/Users/king/Library/Mobile Documents/iCloud~md~obsidian/Documents/King"
CMD_REL="$1"
LOG_NAME="$2"

if [ -z "$CMD_REL" ] || [ -z "$LOG_NAME" ]; then
  echo "用法: loop-runner.sh <命令文件相对vault路径> <日志名>"; exit 2
fi

COMMAND_FILE="$VAULT/$CMD_REL"
LOG="$HOME/.claude/${LOG_NAME}.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "" >> "$LOG"
echo "===== $TIMESTAMP 开始: $CMD_REL =====" >> "$LOG"

cd "$VAULT" || { echo "❌ 无法进入 vault: $VAULT" >> "$LOG"; exit 1; }
command -v claude &>/dev/null || { echo "❌ 找不到 claude 命令" >> "$LOG"; exit 1; }

# 读命令文件，去掉 frontmatter（--- 之间）
INSTRUCTION=$(awk '
  BEGIN { in_front=0; done_front=0 }
  /^---$/ && NR==1 { in_front=1; next }
  /^---$/ && in_front && !done_front { done_front=1; in_front=0; next }
  !in_front { print }
' "$COMMAND_FILE")
[ -z "$INSTRUCTION" ] && { echo "❌ 命令文件为空或不存在: $COMMAND_FILE" >> "$LOG"; exit 1; }

# Sonnet + 跳过权限（无人值守必需）+ 失败重试 3 次（扛代理偶尔掐断）
MAX_TRIES=3; EXIT_CODE=1
for i in $(seq 1 $MAX_TRIES); do
  echo "—— 第 $i/$MAX_TRIES 次 $(date '+%H:%M:%S') ——" >> "$LOG"
  claude -p "$INSTRUCTION" --model claude-sonnet-4-6 --dangerously-skip-permissions >> "$LOG" 2>&1
  EXIT_CODE=$?
  [ $EXIT_CODE -eq 0 ] && break
  echo "⚠️ 第 $i 次失败（退出码 $EXIT_CODE），等 15 秒重试…" >> "$LOG"
  sleep 15
done

[ $EXIT_CODE -eq 0 ] && echo "✅ 完成" >> "$LOG" || echo "❌ 重试 $MAX_TRIES 次仍失败——多半是代理掐断了连接，换个稳定节点再跑" >> "$LOG"
echo "===== 结束 =====" >> "$LOG"
