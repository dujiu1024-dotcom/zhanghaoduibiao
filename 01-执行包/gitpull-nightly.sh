#!/bin/bash
# 每小时（01:00–07:00）备份 + 快进拉取
# 备份优先：先产出一份 git bundle，再做任何拉取动作
# 严禁：自动合并、reset --hard、checkout -- .、clean
set -uo pipefail

REPO="/Users/longyi/project/账号对标"
BK="$HOME/backup/账号对标-git"
LOG="$REPO/01-执行包/checks/git-pull.log"
LOCK="/tmp/账号对标-gitpull.lockdir"

mkdir -p "$BK" "$(dirname "$LOG")"
log() { printf '%s\n' "$*" >> "$LOG"; }

# ---------- 时段闸门：只允许 01–07 ----------
now_h=$((10#$(date +%H)))
if [ "${ALLOW_ANY_HOUR:-0}" != "1" ]; then
  if [ "$now_h" -lt 1 ] || [ "$now_h" -gt 7 ]; then
    log "$(date '+%Y-%m-%d %H:%M:%S') | pre=- | post=- | ff=跳过 | backup=- | note=当前 ${now_h} 点，不在 01–07 时段，未执行"
    exit 0
  fi
fi

# ---------- 防重入 ----------
if [ -d "$LOCK" ]; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +60 2>/dev/null)" ]; then
    rmdir "$LOCK" 2>/dev/null
  fi
fi
if ! mkdir "$LOCK" 2>/dev/null; then
  log "$(date '+%Y-%m-%d %H:%M:%S') | pre=- | post=- | ff=跳过 | backup=- | note=上一轮仍在运行（锁 $LOCK 未释放）"
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

stamp=$(date '+%Y%m%d-%H%M')
human=$(date '+%Y-%m-%d %H:%M:%S')
pre=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "无")
pre_short=${pre:0:7}

# ---------- 1. 备份优先 ----------
bundle="$BK/$stamp.bundle"
if git -C "$REPO" bundle create "$bundle.part" --all >>"$LOG" 2>&1 && mv "$bundle.part" "$bundle"; then
  bsize=$(du -h "$bundle" | cut -f1 | tr -d ' ')
  bbytes=$(stat -f %z "$bundle")
  backup_info="backup=$bundle (${bsize}/${bbytes}B)"
else
  rm -f "$bundle.part"
  log "$human | pre=$pre_short | post=$pre_short | ff=跳过 | backup=失败 | note=git bundle 失败，按备份优先原则本轮不拉取"
  exit 1
fi

# ---------- 2. 本地未提交改动：只记录，不动它 ----------
dirty=$(git -C "$REPO" status --porcelain --untracked-files=no)
if [ -n "$dirty" ]; then
  n=$(printf '%s\n' "$dirty" | wc -l | tr -d ' ')
  log "$human | pre=$pre_short | post=$pre_short | ff=跳过 | $backup_info | note=本地有 $n 个未提交改动，未执行 pull（不覆盖本地）"
  exit 0
fi

# ---------- 3. fetch + 快进 ----------
if ! git -C "$REPO" fetch --quiet origin >>"$LOG" 2>&1; then
  log "$human | pre=$pre_short | post=$pre_short | ff=失败 | $backup_info | note=fetch 失败（网络或凭据）"
  exit 1
fi

behind=$(git -C "$REPO" rev-list --count 'HEAD..@{u}' 2>/dev/null || echo 0)
ahead=$(git -C "$REPO" rev-list --count '@{u}..HEAD' 2>/dev/null || echo 0)

if [ "$ahead" -gt 0 ]; then
  log "$human | pre=$pre_short | post=$pre_short | ff=跳过 | $backup_info | note=本地领先远端 $ahead 个提交（可能已分叉），需人工处理"
  exit 0
fi

if [ "$behind" -eq 0 ]; then
  log "$human | pre=$pre_short | post=$pre_short | ff=跳过 | $backup_info | note=已是最新，无需拉取"
  exit 0
fi

if pull_out=$(git -C "$REPO" pull --ff-only --quiet 2>&1); then
  post=$(git -C "$REPO" rev-parse HEAD)
  log "$human | pre=$pre_short | post=${post:0:7} | ff=成功（+$behind 提交）| $backup_info | note="
else
  log "$human | pre=$pre_short | post=$pre_short | ff=失败 | $backup_info | note=ff-only 被拒绝：$(printf '%s' "$pull_out" | tr '\n' ' ' | cut -c1-300)"
  exit 1
fi
