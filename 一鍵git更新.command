#!/bin/bash
# ===================================================================
#  All-in-one tool for students: install Git (if missing) + UPDATE  -- macOS
#  What it does:
#    0) If Git is not installed -> install it (Xcode CLT, or Homebrew)
#    1) If this folder is a ZIP download (not a git repo) -> link it to
#       the teacher's repository so you can pull from now on
#    2) Backs up any teacher file you edited into a timestamped folder
#         _my_backup_<time>/...   (no data loss)
#    3) Restores the originals, then pulls the teacher's latest version
#    4) Your own NEW files (untracked) are NEVER touched
#  Usage: put this .command in the project (repo) ROOT folder.
#         First time: right-click > Open  (to bypass Gatekeeper),
#         after that you can double-click it.
#         If "permission denied", run once:  chmod +x "一鍵git更新.command"
# ===================================================================
set -u
cd "$(dirname "$0")" || exit 1

# Teacher's repository (used to auto-link ZIP-downloaded folders)
REPO_URL="https://github.com/ms-112-scott/DF26_ws18.git"

echo ""
echo "===== AUTO UPDATE START ====="
echo ""

# ============================================================
#  STEP 0: make sure Git exists (install it if it does not)
# ============================================================
if ! command -v git >/dev/null 2>&1; then
  echo "[0/4] Git not found. Installing it for you first..."
  echo ""
  if command -v brew >/dev/null 2>&1; then
    echo "      Installing Git via Homebrew ..."
    brew install git
  elif command -v xcode-select >/dev/null 2>&1; then
    echo "      Asking macOS to install the Command Line Tools (includes Git)..."
    echo "      A system dialog should pop up -> click 'Install' and wait."
    xcode-select --install 2>/dev/null
  fi
  # Re-check (a fresh install may not be on PATH in this same window)
  if ! command -v git >/dev/null 2>&1; then
    echo ""
    echo "[OK] After Git finishes installing, please run this file AGAIN."
    read -r -p "Press Enter to close..." _
    exit 0
  fi
fi
echo "[0/4] Git found: $(git --version)"
echo ""

# ============================================================
#  STEP 1: connect this folder to Git if it is a ZIP download
# ============================================================
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[LINK] This folder is not connected to Git yet (ZIP download?)."
  echo "       Connecting it to the teacher's repository so you can pull later..."
  echo ""
  if [ ! -f "requirements.txt" ]; then
    echo "[ERROR] This does not look like the course folder"
    echo "        (requirements.txt not found next to this file)."
    echo "        Put this file in the extracted project folder, then run again."
    read -r -p "Press Enter to close..." _
    exit 1
  fi
  git init >/dev/null 2>&1
  git remote remove origin >/dev/null 2>&1
  git remote add origin "$REPO_URL"
  echo "       Fetching from $REPO_URL ..."
  if ! git fetch origin; then
    echo "[ERROR] Could not reach the remote. Check your internet connection"
    echo "        and run this file again."
    read -r -p "Press Enter to close..." _
    exit 1
  fi
  # Detect the default branch on the remote (master or main)
  DEFBR=""
  git show-ref --verify --quiet refs/remotes/origin/master && DEFBR="master"
  if [ -z "$DEFBR" ]; then
    git show-ref --verify --quiet refs/remotes/origin/main && DEFBR="main"
  fi
  [ -z "$DEFBR" ] && DEFBR="master"
  # Point HEAD/index at the remote WITHOUT deleting your files yet
  git reset "origin/$DEFBR" >/dev/null 2>&1
  git branch -M "$DEFBR" >/dev/null 2>&1
  git branch --set-upstream-to="origin/$DEFBR" "$DEFBR" >/dev/null 2>&1
  echo "       Linked to branch: $DEFBR"
  echo ""
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

echo "[2/4] Backing up files you edited into a timestamped folder (if any)..."
TS="$(date +%Y%m%d_%H%M%S)"
BK="_my_backup_$TS"
EDITED=()
while IFS= read -r _line; do
  [ -n "$_line" ] && EDITED+=("$_line")
done < <(git -c core.quotepath=false diff --name-only HEAD)
if [ "${#EDITED[@]}" -eq 0 ]; then
  echo "      (no local edits to back up)"
else
  for p in "${EDITED[@]}"; do
    [ -e "$p" ] || continue
    dest="$BK/$p"
    mkdir -p "$(dirname "$dest")"
    cp -f "$p" "$dest"
    echo "      backup: $p"
  done
  echo "      -> all saved in folder: $BK"
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
echo "Your edits (if any) were saved in a  _my_backup_<time>  folder - check anytime."
echo ""
read -r -p "Press Enter to close..." _
