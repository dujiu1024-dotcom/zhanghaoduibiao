#!/bin/bash
# 事件驱动的便宜检查：入库结束（rag.py ingest 钩子）或 metadata.csv 被改动后跑
# data/gate/e0/copy 四项，不含 recall（recall 一轮 5–7 分钟，只放在每日 20:30 兜底里）。
#
# 触发点两处：
#   1) 04-知识底座/rag/rag.py 的 cmd_ingest 结束处（手工跑 rag.py ingest 也覆盖）
#   2) launchd com.changhao.checks.event 监听 knowledge/sources/metadata.csv
#
# 去抖 60 秒 + 目录锁互斥：一次 ingest 常伴随多次文件事件，重复触发直接丢弃；
# 已有检查在跑时也丢弃（每日 20:30 兜底会补上）。
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHECKS="$ROOT/01-执行包/checks"
LOG="$CHECKS/event.log"
LOCK="$CHECKS/.event.lock"
STAMP="$CHECKS/.event.last"
REASON="${1:-manual}"
mkdir -p "$CHECKS"

now=$(date +%s)
if [ -f "$STAMP" ] && [ $((now - $(cat "$STAMP" 2>/dev/null || echo 0))) -lt 60 ]; then
  echo "$(date '+%F %T') skip（${REASON}）：60 秒内已触发过" >> "$LOG"
  exit 0
fi
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "$(date '+%F %T') skip（${REASON}）：已有检查在跑" >> "$LOG"
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
echo "$now" > "$STAMP"

echo "===== $(date '+%F %T') 触发：${REASON}" >> "$LOG"
"$ROOT/01-执行包/run_all_checks.sh" --only "${CHECK_ONLY:-data,gate,e0,copy}" >> "$LOG" 2>&1
code=$?
echo "===== $(date '+%F %T') 退出码 $code" >> "$LOG"
# 日志留最近 400 行，避免无界增长
tail -n 400 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
exit "$code"
