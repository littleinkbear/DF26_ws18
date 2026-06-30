#!/bin/bash
# ===================================================================
#  Auto-update tool for students  (clone / pull workflow)  -- macOS
#  What it does:
#    1) Backs up any teacher file you edited as  name-1.ext  (no data loss)
#    2) Restores the originals, then pulls the teacher's latest version
#    3) Your own NEW files (untracked) are NEVER touched
#  Usage: put this .command in the project (repo) ROOT folder.
#         First time: right-click > Open  (to bypass Gatekeeper),
#         after that you can double-click it.
#         If "permission denied", run once:  chmod +x "一鍵git更新.command"
# ===================================================================
set -u
cd "$(dirname "$0")" || exit 1

echo ""
echo "===== AUTO UPDATE START ====="
echo ""

if ! command -v git >/dev/null 2>&1; then
  echo "[ERROR] Git not found. Please install Git first: https://git-scm.com"
  echo "        (or run: xcode-select --install)"
  read -r -p "Press Enter to close..." _
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[ERROR] This folder is not a git project."
  echo "        Put this file inside the cloned project folder, then run again."
  read -r -p "Press Enter to close..." _
  exit 1
fi

# --- Clear any stuck git state (interrupted merge/rebase, stale lock) ---
[ -f ".git/index.lock" ] && rm -f ".git/index.lock" >/dev/null 2>&1
git merge --abort >/dev/null 2>&1
git rebase --abort >/dev/null 2>&1
git cherry-pick --abort >/dev/null 2>&1

echo "[1/4] Fetching from remote..."
git fetch origin
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "      Current branch: $BRANCH"
echo ""

echo "[2/4] Backing up files you edited (if any)..."
EDITED=()
while IFS= read -r _line; do
  [ -n "$_line" ] && EDITED+=("$_line")
done < <(git -c core.quotepath=false diff --name-only HEAD)
if [ "${#EDITED[@]}" -eq 0 ]; then
  echo "      (no local edits to back up)"
else
  for p in "${EDITED[@]}"; do
    [ -z "$p" ] && continue
    [ -e "$p" ] || continue
    d="$(dirname "$p")"
    base="$(basename "$p")"
    if [[ "$base" == *.* ]]; then
      ext=".${base##*.}"
      stem="${base%.*}"
    else
      ext=""
      stem="$base"
    fi
    n=1
    while :; do
      cand="$stem-$n$ext"
      [ "$d" != "." ] && cand="$d/$stem-$n$ext"
      [ -e "$cand" ] || break
      n=$((n+1))
    done
    cp -f "$p" "$cand"
    echo "      backup: $p  ->  $(basename "$cand")"
  done
fi
echo ""

echo "[3/4] Restoring originals to teacher's version..."
git reset --hard HEAD >/dev/null 2>&1
echo ""

echo "[4/4] Updating to latest (git pull)..."
if ! git pull origin "$BRANCH"; then
  echo ""
  echo "      Normal pull failed. Force-syncing to remote latest..."
  echo "      (your edits are already backed up; practice files are safe)"
  git reset --hard "origin/$BRANCH"
fi

echo ""
echo "===== DONE.  You are now on the teacher's latest version. ====="
echo "Your edits (if any) were saved as  name-1.ext  - check them anytime."
echo ""
read -r -p "Press Enter to close..." _
