#!/bin/bash
# 每小时（01:00–07:00）备份 + 快进拉取
# 顺序：备份 → stash 本地改动 → pull --ff-only → stash pop
# 严禁：自动合并、rebase、reset --hard、checkout -- .、clean
set -uo pipefail

REPO="${GITPULL_REPO:-/Users/longyi/project/账号对标}"
BK="${GITPULL_BACKUP_DIR:-$HOME/backup/账号对标-git}"
LOG="${GITPULL_LOG:-$REPO/01-执行包/checks/git-pull.log}"
LOCK="${GITPULL_LOCK:-/tmp/账号对标-gitpull.lockdir}"

mkdir -p "$BK" "$(dirname "$LOG")"
log() { printf '%s\n' "$*" >> "$LOG"; }

# ---------- 时段闸门：只允许 01–07 ----------
now_h=$((10#$(date +%H)))
if [ "${ALLOW_ANY_HOUR:-0}" != "1" ]; then
  if [ "$now_h" -lt 1 ] || [ "$now_h" -gt 7 ]; then
    log "$(date '+%Y-%m-%d %H:%M:%S') | pre=- | post=- | ff=跳过 | stash=否 | pop=- | backup=- | note=当前 ${now_h} 点，不在 01–07 时段，未执行"
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
  log "$(date '+%Y-%m-%d %H:%M:%S') | pre=- | post=- | ff=跳过 | stash=否 | pop=- | backup=- | note=上一轮仍在运行（锁 $LOCK 未释放）"
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
  log "$human | pre=$pre_short | post=$pre_short | ff=跳过 | stash=否 | pop=- | backup=失败 | note=git bundle 失败，按备份优先原则本轮不拉取"
  exit 1
fi

# ---------- 2. 有本地改动则 stash（不抓未跟踪文件） ----------
stash_info="否"
stash_msg="auto-nightly-$stamp"
stashed=0
porcelain=$(git -C "$REPO" status --porcelain)
if [ -n "$porcelain" ]; then
  before_n=$(git -C "$REPO" stash list | wc -l | tr -d ' ')
  if git -C "$REPO" stash push -m "$stash_msg" >>"$LOG" 2>&1; then
    after_n=$(git -C "$REPO" stash list | wc -l | tr -d ' ')
    if [ "$after_n" -gt "$before_n" ]; then
      stashed=1
      stash_info="是（$(git -C "$REPO" stash list | head -1 | cut -d: -f1) \"$stash_msg\"）"
    else
      stash_info="否（只有未跟踪文件，stash 未产生条目）"
    fi
  else
    log "$human | pre=$pre_short | post=$pre_short | ff=跳过 | stash=失败 | pop=- | $backup_info | note=git stash 失败，本轮不拉取，工作区未动"
    exit 1
  fi
fi

# stash 之后 HEAD 仍是 pre，供兜底恢复
restore_stash() {
  # $1 = 已在日志里说明过的原因；只把改动放回，不解决冲突
  if [ "$stashed" -eq 1 ]; then
    if git -C "$REPO" stash pop >/dev/null 2>&1; then
      printf '%s' "成功"
    else
      printf '%s' "冲突（改动仍在 stash 中，需人工处理：git stash list / git stash pop）"
    fi
  else
    printf '%s' "-"
  fi
}

# ---------- 3. fetch + 快进 ----------
if ! git -C "$REPO" fetch --quiet origin >>"$LOG" 2>&1; then
  pop_state=$(restore_stash)
  log "$human | pre=$pre_short | post=$pre_short | ff=失败 | stash=$stash_info | pop=$pop_state | $backup_info | note=fetch 失败（网络或凭据）"
  exit 1
fi

behind=$(git -C "$REPO" rev-list --count 'HEAD..@{u}' 2>/dev/null || echo 0)
ahead=$(git -C "$REPO" rev-list --count '@{u}..HEAD' 2>/dev/null || echo 0)

if [ "$ahead" -gt 0 ]; then
  pop_state=$(restore_stash)
  log "$human | pre=$pre_short | post=$pre_short | ff=跳过 | stash=$stash_info | pop=$pop_state | $backup_info | note=本地领先远端 $ahead 个提交（已分叉），不做 rebase/合并，需人工处理"
  exit 0
fi

if [ "$behind" -eq 0 ]; then
  pop_state=$(restore_stash)
  log "$human | pre=$pre_short | post=$pre_short | ff=跳过 | stash=$stash_info | pop=$pop_state | $backup_info | note=已是最新，无需拉取"
  exit 0
fi

if pull_out=$(git -C "$REPO" pull --ff-only --quiet 2>&1); then
  post=$(git -C "$REPO" rev-parse HEAD)
  pop_state=$(restore_stash)
  log "$human | pre=$pre_short | post=${post:0:7} | ff=成功（+$behind 提交）| stash=$stash_info | pop=$pop_state | $backup_info | note="
else
  pop_state=$(restore_stash)
  log "$human | pre=$pre_short | post=$pre_short | ff=失败 | stash=$stash_info | pop=$pop_state | $backup_info | note=ff-only 被拒绝：$(printf '%s' "$pull_out" | tr '\n' ' ' | cut -c1-300)"
  exit 1
fi
