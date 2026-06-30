#!/bin/bash
# ============================================================
#  一键更新虚拟环境检查（单文件 · macOS · 双击即可运行）
#   1. 检测是否有 Python 3.14，无则用 Homebrew 自动安装
#      （没有 brew 则回退下载 python.org 官方 .pkg 安装）
#   2. 检查项目 .venv 是否为 3.14，不符则删除重建
#   3. 升级 pip 并安装 / 更新 requirements.txt
#   4. 某个包固定版本失败 -> 自动改用不固定版本重试；仍失败 -> 红字警告
#  可重复运行；requirements.txt 更新后再双击一次即可同步。
#
#  首次使用：右键 > 打开（绕过 Gatekeeper）；之后可直接双击。
#  若提示 permission denied，先执行一次：
#      chmod +x "一鍵虛擬環境更新.command"
# ============================================================
set -u
cd "$(dirname "$0")" || exit 1

PYVER='3.14'
PYFULL='3.14.6'
ROOT="$(pwd)"
VENV="$ROOT/.venv"
VPY="$VENV/bin/python"
REQ="$ROOT/requirements.txt"

# ---- 颜色输出 ----
C_CYAN=$'\033[36m'; C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'; C_RED=$'\033[31m'; C_OFF=$'\033[0m'
Info(){ printf '%s%s%s\n' "$C_CYAN"  "$1" "$C_OFF"; }
Ok(){   printf '%s%s%s\n' "$C_GREEN" "$1" "$C_OFF"; }
Warn(){ printf '%s%s%s\n' "$C_YELLOW" "$1" "$C_OFF"; }
Err(){  printf '%s%s%s\n' "$C_RED"   "$1" "$C_OFF"; }
Finish(){ echo ""; read -r -p "按 Enter 键关闭窗口" _ ; exit "$1"; }

# 找到 python3.14 可执行档（brew、python.org、PATH 都试）
find_py() {
  for c in "python$PYVER" "/opt/homebrew/bin/python$PYVER" "/usr/local/bin/python$PYVER" \
           "/Library/Frameworks/Python.framework/Versions/$PYVER/bin/python$PYVER"; do
    if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then
      "$c" --version >/dev/null 2>&1 && { echo "$c"; return 0; }
    fi
  done
  return 1
}

# ---- 官方 .pkg 回退安装（无 brew 时） ----
install_python_official() {
  local arch pkg url
  arch="$(uname -m)"
  url="https://www.python.org/ftp/python/$PYFULL/python-$PYFULL-macos11.pkg"
  pkg="$(mktemp -t python-$PYFULL).pkg"
  Info "    从 python.org 下载安装包 $PYFULL ..."
  if ! curl -L --fail -o "$pkg" "$url"; then
    Err "       下载失败，请手动安装 https://www.python.org/downloads/"
    return 1
  fi
  Info "    安装中（需要输入管理员密码）..."
  if ! sudo installer -pkg "$pkg" -target /; then
    Err "[错误] 安装程序返回错误。"
    rm -f "$pkg"
    return 1
  fi
  rm -f "$pkg"
  return 0
}

Info "[项目根目录] $ROOT"
echo ""

# ---- 1. 确认有 Python 3.14 ----
Info "[1/4] 检查 Python $PYVER ..."
PYBIN="$(find_py || true)"
if [ -z "${PYBIN:-}" ]; then
  Warn "    找不到 Python $PYVER，尝试自动安装..."
  installed=0
  if command -v brew >/dev/null 2>&1; then
    Info "    使用 Homebrew 安装 python@$PYVER ..."
    brew install "python@$PYVER"
    PYBIN="$(find_py || true)"
    [ -n "${PYBIN:-}" ] && installed=1 || Warn "    brew 安装未生效，改用官方安装包回退方案..."
  else
    Warn "    找不到 Homebrew，改用官方安装包回退方案..."
  fi
  if [ "$installed" -eq 0 ]; then
    if install_python_official; then
      PYBIN="$(find_py || true)"
      [ -n "${PYBIN:-}" ] && installed=1
    fi
  fi
  if [ "$installed" -eq 0 ]; then
    Err "[错误] Python $PYVER 安装后仍无法调用。"
    Err "       请关闭并重开此窗口后再双击运行一次。"
    Finish 1
  fi
fi
Ok  "    全局 $("$PYBIN" --version 2>&1)"
echo ""

# ---- 2. 检查现有 .venv 版本是否正确 ----
Info "[2/4] 检查 .venv ..."
needCreate=1
if [ -x "$VPY" ]; then
  cur="$("$VPY" --version 2>&1)"
  echo "    现有 .venv $cur"
  case "$cur" in
    "Python $PYVER."*) needCreate=0 ;;
    *) Warn "    版本不符 $PYVER，删除重建..."; rm -rf "$VENV" ;;
  esac
fi

# ---- 3. 创建 .venv ----
if [ "$needCreate" -eq 1 ]; then
  Info "[3/4] 用 Python $PYVER 创建 .venv ..."
  if ! "$PYBIN" -m venv "$VENV" || [ ! -x "$VPY" ]; then
    Err "[错误] 创建虚拟环境失败。"
    Finish 1
  fi
else
  Info "[3/4] .venv 已是 $PYVER，跳过创建。"
fi
echo ""

# ---- 4. 安装 / 更新 requirements ----
Info "[4/4] 升级 pip 并安装 / 更新软件包 ..."
"$VPY" -m pip install --upgrade pip
if [ ! -f "$REQ" ]; then
  Warn "[警告] 找不到 requirements.txt，跳过软件包安装。"
  Ok "完成。虚拟环境就绪 $VENV"
  Finish 0
fi

Info "    先尝试按 requirements.txt 整体安装 ..."
if "$VPY" -m pip install -r "$REQ"; then
  echo ""
  Ok "============================================================"
  Ok " 完成。虚拟环境就绪 $VENV"
  Ok " 启动命令 source .venv/bin/activate"
  Ok "============================================================"
  Finish 0
fi

echo ""
Warn "    整体安装失败，改为逐行安装；某行失败时自动改用不固定版本重试 ..."
failed=()
while IFS= read -r raw || [ -n "$raw" ]; do
  line="$(printf '%s' "$raw" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  [ -z "$line" ] && continue
  case "$line" in \#*) continue ;; esac

  if ! "$VPY" -m pip install "$line"; then
    pkg="$(printf '%s' "$line" | sed -E 's/[<>=!~;[ ].*$//')"
    Warn "       固定版本失败，改用不固定版本重试 $pkg"
    if ! "$VPY" -m pip install "$pkg"; then
      failed+=("$pkg")
    fi
  fi
done < "$REQ"

if [ "${#failed[@]}" -gt 0 ]; then
  echo ""
  Err "============================================================"
  Err "[错误] 以下软件包安装失败（固定与不固定版本均失败）:"
  Err "   ${failed[*]}"
  Err "请手动检查网络 / 包名 / requirements.txt 后重试。"
  Err "============================================================"
  Finish 1
fi

echo ""
Ok "============================================================"
Ok " 完成。虚拟环境就绪 $VENV"
Ok " 启动命令 source .venv/bin/activate"
Ok "============================================================"
Finish 0
