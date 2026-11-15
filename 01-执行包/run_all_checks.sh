#!/bin/bash
# 统一检查入口：四道闸 + 检索验收，出 PASS/FAIL、写快照、与上次比数字。
# 用法：
#   ./01-执行包/run_all_checks.sh                # 全跑（约 7–10 分钟）
#   ./01-执行包/run_all_checks.sh --fast         # 跳过 recall
#   ./01-执行包/run_all_checks.sh --only gate,data
#   ./01-执行包/run_all_checks.sh --strict       # 未达标也算失败
# 退出码：0 全绿 / 1 有回归或崩溃 / 2 有未达标项但与上次持平。
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
exec python3 -u "01-执行包/run_all_checks.py" "$@"
