#!/usr/bin/env bash
# update-all-skills.sh — 更新本机各 Agent 已安装的 skills
# 覆盖：skills.sh / Cursor / Claude / Hermes / Codex / Gemini / Antigravity /
#        Trae / Copilot / OpenCode / Windsurf / Crush / Deep Agents / OpenClaw /
#        Agent Reach / 43* 等（存在则更新，缺失则跳过）
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="${REPORT_DIR:-$HOME/.cache/update-all-skills}"
REPORT_FILE="$REPORT_DIR/last-report.txt"
COUNTS_TSV="$REPORT_DIR/last-counts.tsv"
TS="$(date '+%Y-%m-%d %H:%M:%S')"
NPM_REGISTRY="${NPM_REGISTRY:-https://registry.npmjs.org}"
SKIP_HERMES_AGENT_UPDATE="${SKIP_HERMES_AGENT_UPDATE:-0}"

mkdir -p "$REPORT_DIR"
: >"$REPORT_FILE"
: >"$COUNTS_TSV"

# label|path — skills.sh 生态 + 常见额外 root
PLATFORM_ROOTS="
cursor|$HOME/.cursor/skills
agents|$HOME/.agents/skills
claude|$HOME/.claude/skills
codex|$HOME/.codex/skills
hermes|$HOME/.hermes/skills
gemini|$HOME/.gemini/skills
antigravity|$HOME/.gemini/antigravity/skills
antigravity-cli|$HOME/.gemini/antigravity-cli/skills
trae|$HOME/.trae/skills
trae-cn|$HOME/.trae-cn/skills
copilot|$HOME/.copilot/skills
ghcp|$HOME/.ghcp-appmod/skills
opencode|$HOME/.config/opencode/skills
windsurf|$HOME/.codeium/windsurf/skills
crush|$HOME/.config/crush/skills
deepagents|$HOME/.deepagents/agent/skills
openclaw|$HOME/.openclaw/skills
"

# colors (disabled if not tty)
if [[ -t 1 ]]; then
  C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_ERR=$'\033[31m'; C_DIM=$'\033[2m'; C_RST=$'\033[0m'; C_BOLD=$'\033[1m'
else
  C_OK=; C_WARN=; C_ERR=; C_DIM=; C_RST=; C_BOLD=
fi

declare -a RESULTS=()
OK_N=0; WARN_N=0; FAIL_N=0; SKIP_N=0

log()  { echo "$*" | tee -a "$REPORT_FILE"; }
hr()   { log "────────────────────────────────────────"; }
section() { hr; log "${C_BOLD}▶ $*${C_RST}"; }

record() {
  # record <status> <scope> <message>
  local st="$1" scope="$2" msg="$3"
  case "$st" in
    ok)   OK_N=$((OK_N + 1));   log "  ${C_OK}✓${C_RST} [$scope] $msg" ;;
    warn) WARN_N=$((WARN_N + 1)); log "  ${C_WARN}!${C_RST} [$scope] $msg" ;;
    fail) FAIL_N=$((FAIL_N + 1)); log "  ${C_ERR}✗${C_RST} [$scope] $msg" ;;
    skip) SKIP_N=$((SKIP_N + 1)); log "  ${C_DIM}·${C_RST} [$scope] $msg" ;;
  esac
  RESULTS+=("$st|$scope|$msg")
}

have() { command -v "$1" >/dev/null 2>&1; }

run_capture() {
  # run_capture <cmd...>  → sets CAP_OUT / CAP_EC
  local tmp
  tmp="$(mktemp)"
  set +e
  "$@" >"$tmp" 2>&1
  CAP_EC=$?
  CAP_OUT="$(cat "$tmp")"
  rm -f "$tmp"
  return 0
}

# ── curl helper: download if remote differs ──────────────────────────
fetch_if_changed() {
  # fetch_if_changed <url> <dest> → 0 updated, 1 same, 2 fail
  local url="$1" dest="$2" tmp
  tmp="$(mktemp)"
  if ! curl -fsSL --connect-timeout 15 --max-time 60 "$url" -o "$tmp" 2>/dev/null; then
    rm -f "$tmp"
    return 2
  fi
  if [[ -f "$dest" ]] && cmp -s "$tmp" "$dest"; then
    rm -f "$tmp"
    return 1
  fi
  mkdir -p "$(dirname "$dest")"
  mv "$tmp" "$dest"
  return 0
}

# ── inventory ────────────────────────────────────────────────────────
count_skills_under() {
  local root="$1"
  [[ -d "$root" ]] || { echo 0; return; }
  find "$root" -type f -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' '
}

list_skill_names_under() {
  local root="$1"
  [[ -d "$root" ]] || return 0
  find "$root" -type f -name 'SKILL.md' 2>/dev/null | while read -r f; do
    local dir; dir="$(dirname "$f")"
    # skip archives / caches / node_modules
    case "$dir" in
      */.archive/*|*/node_modules/*|*/.hub/*|*/.curator_backups/*) continue ;;
    esac
    basename "$dir"
  done | sort -u
}

# ═════════════════════════════════════════════════════════════════════
log "${C_BOLD}更新本机 Skills — $TS${C_RST}"
log "报告: $REPORT_FILE"
hr

# Snapshot before
log "安装盘点（更新前 SKILL.md 数；仅列出目录存在的平台）:"
echo "phase	label	path	count" >"$COUNTS_TSV"
while IFS='|' read -r label path; do
  [[ -z "${label:-}" ]] && continue
  if [[ -d "$path" ]]; then
    n=$(count_skills_under "$path")
    printf '  %-18s %s\n' "$label" "$n  ($path)" | tee -a "$REPORT_FILE"
    echo "before	$label	$path	$n" >>"$COUNTS_TSV"
  fi
done <<EOF
$(echo "$PLATFORM_ROOTS" | sed '/^[[:space:]]*$/d')
EOF

# ═════════════════════════════════════════════════════════════════════
# 1) skills.sh CLI（跨 Cursor / Claude / Hermes / Codex / Trae / Gemini…）
# ═════════════════════════════════════════════════════════════════════
section "skills.sh（npx skills update）"

SKILLS_BIN=""
if have skills; then
  SKILLS_BIN="skills"
elif have npx; then
  SKILLS_BIN="npx --yes --registry $NPM_REGISTRY skills"
fi

if [[ -n "$SKILLS_BIN" ]]; then
  # shellcheck disable=SC2086
  run_capture $SKILLS_BIN list -g --json
  if [[ $CAP_EC -eq 0 ]]; then
    GLOBAL_N=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else 0)' <<<"$CAP_OUT" 2>/dev/null || echo 0)
    record ok "skills.sh" "发现 $GLOBAL_N 个全局 skill（list -g）"
  else
    record warn "skills.sh" "list -g 失败: $(echo "$CAP_OUT" | tail -1)"
  fi

  # shellcheck disable=SC2086
  run_capture $SKILLS_BIN update -g -y
  if [[ $CAP_EC -eq 0 ]]; then
    if echo "$CAP_OUT" | grep -Eiq 'No global skills tracked|nothing to update|up to date|already'; then
      record ok "skills.sh" "全局 lock 无待更新（多数本地 skill 非 skills add 安装）"
    else
      record ok "skills.sh" "全局更新完成"
      echo "$CAP_OUT" | tee -a "$REPORT_FILE" | tail -20
    fi
  else
    record fail "skills.sh" "update -g 失败 (exit $CAP_EC)"
    echo "$CAP_OUT" | tee -a "$REPORT_FILE" | tail -30
  fi
else
  record skip "skills.sh" "未找到 skills / npx"
fi

# ═════════════════════════════════════════════════════════════════════
# 2) Hermes hub skills + agent 本体（会 sync bundled skills）
# ═════════════════════════════════════════════════════════════════════
section "Hermes"

if have hermes; then
  run_capture hermes skills check
  if [[ $CAP_EC -eq 0 ]]; then
    if echo "$CAP_OUT" | grep -Eiq 'No hub-installed|0 outdated|up to date|nothing'; then
      record ok "hermes" "hub skills：无待更新"
    else
      record ok "hermes" "hub check 完成"
      echo "$CAP_OUT" | tee -a "$REPORT_FILE" | tail -15
    fi
  else
    record warn "hermes" "skills check 异常 (exit $CAP_EC)"
  fi

  run_capture hermes skills update
  if [[ $CAP_EC -eq 0 ]]; then
    record ok "hermes" "skills update 完成"
    echo "$CAP_OUT" | tee -a "$REPORT_FILE" | tail -20
  else
    record fail "hermes" "skills update 失败 (exit $CAP_EC)"
    echo "$CAP_OUT" | tee -a "$REPORT_FILE" | tail -20
  fi

  if [[ "$SKIP_HERMES_AGENT_UPDATE" != "1" ]]; then
    run_capture hermes update --yes
    if [[ $CAP_EC -eq 0 ]]; then
      if echo "$CAP_OUT" | grep -Eiq 'Already up to date|already latest|No update|up to date'; then
        record ok "hermes" "agent 已是最新（bundled skills 已同步）"
      else
        record ok "hermes" "agent 已更新（bundled skills 已同步）"
      fi
      echo "$CAP_OUT" | tee -a "$REPORT_FILE" | tail -25
    else
      record warn "hermes" "agent update 失败 (exit $CAP_EC) — 不影响其余 skill"
      echo "$CAP_OUT" | tee -a "$REPORT_FILE" | tail -25
    fi
  else
    record skip "hermes" "跳过 hermes update（SKIP_HERMES_AGENT_UPDATE=1）"
  fi

  # plugins（若有）
  run_capture hermes plugins update 2>/dev/null || true
  if [[ $CAP_EC -eq 0 ]]; then
    record ok "hermes" "plugins update 完成"
  else
    record skip "hermes" "无 plugins 或 update 不可用"
  fi
else
  record skip "hermes" "未安装 hermes CLI"
fi

# ═════════════════════════════════════════════════════════════════════
# 3) Claude Code marketplaces + plugins
# ═════════════════════════════════════════════════════════════════════
section "Claude Code"

if have claude; then
  run_capture claude plugin marketplace update
  if [[ $CAP_EC -eq 0 ]]; then
    record ok "claude" "marketplace 已更新"
    echo "$CAP_OUT" | tee -a "$REPORT_FILE" | tail -15
  else
    record warn "claude" "marketplace update 失败 (exit $CAP_EC)"
    echo "$CAP_OUT" | tee -a "$REPORT_FILE" | tail -15
  fi

  # Update each installed plugin
  PLUGIN_LIST="$(claude plugin list 2>/dev/null || true)"
  PLUGINS=()
  while IFS= read -r line; do
    # lines like: "  ❯ name@marketplace"
    if [[ "$line" =~ ❯[[:space:]]+([^[:space:]]+) ]]; then
      PLUGINS+=("${BASH_REMATCH[1]}")
    elif [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_.-]+@[a-zA-Z0-9_.-]+)[[:space:]]*$ ]]; then
      PLUGINS+=("${BASH_REMATCH[1]}")
    fi
  done <<<"$PLUGIN_LIST"

  if [[ ${#PLUGINS[@]} -eq 0 ]]; then
    # fallback: parse installed_plugins.json
    if [[ -f "$HOME/.claude/plugins/installed_plugins.json" ]]; then
      while IFS= read -r p; do
        [[ -n "$p" ]] && PLUGINS+=("$p")
      done < <(python3 -c 'import json; d=json.load(open("'"$HOME"'/.claude/plugins/installed_plugins.json")); print("\n".join(d.get("plugins",{}).keys()))' 2>/dev/null)
    fi
  fi

  # marketplace 更新后，部分旧 plugin 可能已改名/下架；用插件名（去掉 @marketplace）尝试更新
  if [[ ${#PLUGINS[@]} -eq 0 ]]; then
    record skip "claude" "未发现已安装 plugin"
  else
    for plug in "${PLUGINS[@]}"; do
      short="${plug%%@*}"
      run_capture claude plugin update "$plug"
      if [[ $CAP_EC -ne 0 ]]; then
        run_capture claude plugin update "$short"
      fi
      if [[ $CAP_EC -eq 0 ]]; then
        record ok "claude" "plugin 更新: $plug"
      else
        # marketplace git pull 已覆盖缓存时，记为 skip 而非 fail
        record warn "claude" "plugin $plug 在 marketplace 中未找到（可能已更名；marketplace 源码已拉取）"
      fi
    done
  fi
else
  record skip "claude" "未安装 claude CLI"
fi

# Git pull marketplaces as belt-and-suspenders
for mp in "$HOME/.claude/plugins/marketplaces/"*; do
  [[ -d "$mp/.git" ]] || continue
  name="$(basename "$mp")"
  run_capture git -C "$mp" pull --ff-only
  if [[ $CAP_EC -eq 0 ]]; then
    if echo "$CAP_OUT" | grep -Eiq 'Already up to date'; then
      record ok "claude-git" "marketplace $name 已是最新"
    else
      record ok "claude-git" "marketplace $name 已拉取: $(echo "$CAP_OUT" | head -1)"
    fi
  else
    record warn "claude-git" "marketplace $name pull 失败"
  fi
done

# ═════════════════════════════════════════════════════════════════════
# 4) Agent Reach（包 + SKILL.md）
# ═════════════════════════════════════════════════════════════════════
section "Agent Reach"

AR_BIN=""
if [[ -x "$HOME/.agent-reach-venv/bin/agent-reach" ]]; then
  AR_BIN="$HOME/.agent-reach-venv/bin/agent-reach"
  AR_PIP="$HOME/.agent-reach-venv/bin/pip"
elif have agent-reach; then
  AR_BIN="agent-reach"
  AR_PIP=""
fi

if [[ -n "$AR_BIN" ]]; then
  OLD_VER="$($AR_BIN --version 2>/dev/null | head -1 || true)"
  run_capture "$AR_BIN" check-update
  CHECK_OUT="$CAP_OUT"

  if [[ -n "${AR_PIP:-}" ]]; then
    run_capture "$AR_PIP" install --upgrade "https://github.com/Panniantong/agent-reach/archive/main.zip"
    if [[ $CAP_EC -eq 0 ]]; then
      NEW_VER="$($AR_BIN --version 2>/dev/null | head -1 || true)"
      if [[ "$OLD_VER" == "$NEW_VER" ]]; then
        record ok "agent-reach" "包已是最新 ($NEW_VER)"
      else
        record ok "agent-reach" "包已升级: $OLD_VER → $NEW_VER"
      fi
    else
      record fail "agent-reach" "pip 升级失败"
      echo "$CAP_OUT" | tee -a "$REPORT_FILE" | tail -20
    fi
  else
    record warn "agent-reach" "未找到 venv pip，跳过包升级（$CHECK_OUT）"
  fi

  run_capture "$AR_BIN" skill --install
  if [[ $CAP_EC -eq 0 ]]; then
    record ok "agent-reach" "SKILL.md 已重新注册到 agent 目录"
  else
    record warn "agent-reach" "skill --install 失败"
  fi

  # Best-effort: upgrade already-installed companion CLIs
  for tool in twitter-cli bilibili-cli xiaohongshu-cli yt-dlp; do
    if have pipx && pipx list 2>/dev/null | grep -Eq "$tool"; then
      run_capture pipx upgrade "$tool"
      [[ $CAP_EC -eq 0 ]] && record ok "agent-reach" "pipx upgrade $tool" || record warn "agent-reach" "pipx upgrade $tool 失败"
    fi
  done
else
  record skip "agent-reach" "未安装"
fi

# ═════════════════════════════════════════════════════════════════════
# 5) 43 生态 + 才虫（有明确远端文件列表的 skill）
# ═════════════════════════════════════════════════════════════════════
section "远端可刷新 Skill（43* / 才虫）"

update_file_set() {
  # update_file_set <label> <dir> <url_builder_fn via nameref list>
  # Uses global UPD_URLS / UPD_DESTS parallel arrays
  local label="$1" dir="$2"
  local updated=0 same=0 fail=0
  local i
  for i in "${!UPD_URLS[@]}"; do
    local url="${UPD_URLS[$i]}" dest="$dir/${UPD_DESTS[$i]}"
    fetch_if_changed "$url" "$dest"
    case $? in
      0) updated=$((updated + 1)) ;;
      1) same=$((same + 1)) ;;
      *) fail=$((fail + 1)) ;;
    esac
  done
  if [[ $fail -gt 0 && $updated -eq 0 && $same -eq 0 ]]; then
    record fail "$label" "刷新失败 (${fail} files download failed)"
  elif [[ $updated -gt 0 ]]; then
    extra=""
    [[ $fail -gt 0 ]] && extra=", ${fail} skipped/404"
    record ok "$label" "updated ${updated} files (${same} unchanged${extra})"
  elif [[ $fail -gt 0 ]]; then
    record warn "$label" "unchanged ${same}, ${fail} files unavailable (404/network)"
  else
    record ok "$label" "already latest (${same} files unchanged)"
  fi
}

# 43chat — 以 skill.json files 列表为准
if [[ -d "$HOME/.hermes/skills/43chat" ]]; then
  DIR="$HOME/.hermes/skills/43chat"
  TS_Q="$(date +%s)"
  UPD_DESTS=()
  UPD_URLS=()
  _43chat_files=()
  while IFS= read -r remote; do
    [[ -n "$remote" ]] && _43chat_files+=("$remote")
  done < <(python3 - <<'PY' 2>/dev/null || true
import json, pathlib
p = pathlib.Path.home() / ".hermes/skills/43chat/skill.json"
files = ["skill.md","friends.md","groups.md","messaging.md","moments.md","rules.md","heartbeat.md","cognition.md","sse.md","skill.json"]
if p.exists():
    try:
        files = json.loads(p.read_text()).get("files") or files
    except Exception:
        pass
for f in files:
    print(f)
PY
)
  if [[ ${#_43chat_files[@]} -eq 0 ]]; then
    _43chat_files=(skill.md friends.md groups.md messaging.md moments.md rules.md heartbeat.md cognition.md sse.md skill.json)
  fi
  for remote in "${_43chat_files[@]}"; do
    case "$remote" in
      skill.md) local_name="SKILL.md" ;;
      friends.md) local_name="FRIENDS.md" ;;
      groups.md) local_name="GROUPS.md" ;;
      messaging.md) local_name="MESSAGING.md" ;;
      moments.md) local_name="MOMENTS.md" ;;
      rules.md) local_name="RULES.md" ;;
      heartbeat.md) local_name="HEARTBEAT.md" ;;
      cognition.md) local_name="COGNITION.md" ;;
      sse.md) local_name="SSE.md" ;;
      *) local_name="$remote" ;;
    esac
    UPD_DESTS+=("$local_name")
    UPD_URLS+=("https://43chat.cn/${remote}?t=$TS_Q")
  done
  update_file_set "43chat" "$DIR"
fi

# 43comic
if [[ -d "$HOME/.hermes/skills/43comic" ]]; then
  DIR="$HOME/.hermes/skills/43comic"
  BASE="https://comic.43music.vip/agentApi/skills"
  UPD_DESTS=(skill.json SKILL.md INSTALL.md GENERATION.md)
  UPD_URLS=(
    "$BASE/skill.json"
    "$BASE/SKILL.md"
    "$BASE/INSTALL.md"
    "$BASE/GENERATION.md"
  )
  update_file_set "43comic" "$DIR"
fi

# 43farm
if [[ -d "$HOME/.hermes/skills/43farm" ]]; then
  DIR="$HOME/.hermes/skills/43farm"
  BASE="https://farm.43chat.cn/skills"
  UPD_DESTS=(skill.json SKILL.md INSTALL.md HEARTBEAT.md GAMEPLAY.md)
  UPD_URLS=(
    "$BASE/skill.json"
    "$BASE/skill.md"
    "$BASE/install.md"
    "$BASE/heartbeat.md"
    "$BASE/gameplay.md"
  )
  update_file_set "43farm" "$DIR"
fi

# 43swap
if [[ -d "$HOME/.hermes/skills/43swap" ]]; then
  DIR="$HOME/.hermes/skills/43swap"
  BASE="https://swap.43chat.cn/skills/43swap"
  UPD_DESTS=(SKILL.md skill.json INSTALL.md HEARTBEAT.md)
  UPD_URLS=(
    "$BASE/SKILL.md"
    "$BASE/skill.json"
    "$BASE/INSTALL.md"
    "$BASE/HEARTBEAT.md"
  )
  update_file_set "43swap" "$DIR"
fi

# 才虫
if [[ -d "$HOME/.hermes/skills/caichong" ]]; then
  DIR="$HOME/.hermes/skills/caichong"
  UPD_DESTS=(SKILL.md PUBLISHER.md WORKER.md HEARTBEAT.md skill.json)
  UPD_URLS=(
    "https://www.caichong.net/skill.md"
    "https://www.caichong.net/publisher.md"
    "https://www.caichong.net/worker.md"
    "https://www.caichong.net/heartbeat.md"
    "https://www.caichong.net/skill.json"
  )
  update_file_set "才虫" "$DIR"
fi

# ═════════════════════════════════════════════════════════════════════
# 6) 任意带 .git 的 skill 目录 ff-pull
# ═════════════════════════════════════════════════════════════════════
section "Git 跟踪的 Skill 目录"

FOUND_GIT=0
while IFS='|' read -r label path; do
  [[ -z "${label:-}" || ! -d "$path" ]] && continue
  while IFS= read -r gitdir; do
    skilldir="$(dirname "$gitdir")"
    case "$skilldir" in
      */.archive/*|*/node_modules/*|*/.hub/*|*/.system/*) continue ;;
    esac
    FOUND_GIT=$((FOUND_GIT + 1))
    name="$(basename "$skilldir")"
    run_capture git -C "$skilldir" pull --ff-only
    if [[ $CAP_EC -eq 0 ]]; then
      if echo "$CAP_OUT" | grep -Eiq 'Already up to date'; then
        record ok "git" "$label/$name 已是最新"
      else
        record ok "git" "$label/$name 已拉取"
      fi
    else
      record warn "git" "$label/$name pull 失败"
    fi
  done < <(find "$path" -type d -name '.git' 2>/dev/null)
done <<EOF
$(echo "$PLATFORM_ROOTS" | sed '/^[[:space:]]*$/d')
EOF
[[ $FOUND_GIT -eq 0 ]] && record skip "git" "未发现带 .git 的已安装 skill"

# ═════════════════════════════════════════════════════════════════════
# 7) 项目级 .cursor/skills（Desktop 常见）
# ═════════════════════════════════════════════════════════════════════
section "项目级 skills（扫描常见工作区）"

PROJ_FOUND=0
PROJ_SCAN_ROOTS=("$HOME/Desktop" "$HOME/Documents" "$HOME/Projects" "$HOME/dev" "$HOME/code" "$HOME/src")
# Also include current working directory tree (shallow)
PROJ_SCAN_ROOTS+=("$PWD")

_proj_find_args=()
for _r in "${PROJ_SCAN_ROOTS[@]}"; do
  [[ -d "$_r" ]] && _proj_find_args+=("$_r")
done

while IFS= read -r pdir; do
  [[ -n "${pdir:-}" ]] || continue
  PROJ_FOUND=$((PROJ_FOUND + 1))
  n=$(count_skills_under "$pdir")
  # .cursor/skills -> project root is ../..
  proj="$(cd "$pdir/../.." && pwd 2>/dev/null || true)"
  if [[ -n "$SKILLS_BIN" && -n "$proj" && -f "$proj/skills-lock.json" ]]; then
    # shellcheck disable=SC2086
    run_capture bash -c "cd \"$proj\" && $SKILLS_BIN update -p -y"
    if [[ $CAP_EC -eq 0 ]]; then
      record ok "project" "$proj - skills update -p"
    else
      record warn "project" "$proj - update failed"
    fi
  else
    record skip "project" "${pdir} (${n} SKILL.md, no skills-lock)"
  fi
done < <(
  if [[ ${#_proj_find_args[@]} -gt 0 ]]; then
    find "${_proj_find_args[@]}" -maxdepth 5 -type d \( \
      -path '*/.cursor/skills' -o \
      -path '*/.claude/skills' -o \
      -path '*/.trae/skills' -o \
      -path '*/.agents/skills' -o \
      -path '*/.opencode/skills' -o \
      -path '*/.windsurf/skills' -o \
      -path '*/.crush/skills' \
    \) 2>/dev/null | sort -u
  fi
)

[[ $PROJ_FOUND -eq 0 ]] && record skip "project" "未发现项目级 skills 目录"

# ═════════════════════════════════════════════════════════════════════
# 8) 本地-only 盘点（无法自动更新的）
# ═════════════════════════════════════════════════════════════════════
section "本地-only / 系统托管（无法从远端自动更新）"

LOCAL_NOTES=()
# Cursor user skills without lock
if [[ -d "$HOME/.cursor/skills" ]]; then
  while IFS= read -r name; do
    LOCAL_NOTES+=("cursor:$name")
  done < <(list_skill_names_under "$HOME/.cursor/skills")
fi
# Hermes local (non hub) — just count
if have hermes; then
  run_capture hermes skills list
  LOCAL_HERMES=$(echo "$CAP_OUT" | grep -c 'local' || true)
  BUILTIN_HERMES=$(echo "$CAP_OUT" | grep -c 'builtin' || true)
  record skip "inventory" "Hermes: ~${LOCAL_HERMES:-?} local / ~${BUILTIN_HERMES:-?} builtin（local 无 hub 源则不会被 skills update 覆盖）"
fi

record skip "inventory" "Cursor 内置 skills-cursor/ 由 Cursor 托管，本脚本不改动"
record skip "inventory" "Codex ~/.codex/skills/.system 由 Codex 托管"
if [[ ${#LOCAL_NOTES[@]} -gt 0 ]]; then
  record skip "inventory" "用户级本地 skill: ${LOCAL_NOTES[*]}"
fi

# ═════════════════════════════════════════════════════════════════════
# Summary
# ═════════════════════════════════════════════════════════════════════
hr
log "${C_BOLD}结果汇总${C_RST}"
log "  成功 $OK_N  |  警告 $WARN_N  |  失败 $FAIL_N  |  跳过 $SKIP_N"
log "安装盘点（更新后 SKILL.md 数）:"
COUNTS_JSON_TMP="$(mktemp)"
echo '{' >"$COUNTS_JSON_TMP"
first=1
while IFS='|' read -r label path; do
  [[ -z "${label:-}" ]] && continue
  if [[ -d "$path" ]]; then
    n=$(count_skills_under "$path")
    printf '  %-18s %s\n' "$label" "$n  ($path)" | tee -a "$REPORT_FILE"
    echo "after	$label	$path	$n" >>"$COUNTS_TSV"
    if [[ $first -eq 1 ]]; then first=0; else echo ',' >>"$COUNTS_JSON_TMP"; fi
    printf '  "%s": %s' "$label" "$n" >>"$COUNTS_JSON_TMP"
  fi
done <<EOF
$(echo "$PLATFORM_ROOTS" | sed '/^[[:space:]]*$/d')
EOF
echo '' >>"$COUNTS_JSON_TMP"
echo '}' >>"$COUNTS_JSON_TMP"
log "完整报告: $REPORT_FILE"
hr

# machine-readable summary for callers
SUMMARY_JSON="$REPORT_DIR/last-summary.json"
RESULTS_FILE="$REPORT_DIR/last-results.tsv"
printf '%s\n' "${RESULTS[@]}" >"$RESULTS_FILE"
python3 - "$SUMMARY_JSON" "$RESULTS_FILE" "$COUNTS_JSON_TMP" "$TS" "$OK_N" "$WARN_N" "$FAIL_N" "$SKIP_N" <<'PY'
import json, sys
path, results_file, counts_file, ts, ok, warn, fail, skip = sys.argv[1:9]
parsed = []
with open(results_file, encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            parsed.append({"status": parts[0], "scope": parts[1], "message": parts[2]})
with open(counts_file, encoding="utf-8") as f:
    counts = json.load(f)
out = {
    "timestamp": ts,
    "ok": int(ok),
    "warn": int(warn),
    "fail": int(fail),
    "skip": int(skip),
    "counts": counts,
    "results": parsed,
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(path)
PY
rm -f "$COUNTS_JSON_TMP"

exit $(( FAIL_N > 0 ? 1 : 0 ))
