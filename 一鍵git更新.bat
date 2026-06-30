@echo off
REM ===================================================================
REM  All-in-one tool for students: AUTO-INSTALL Git (if missing) + UPDATE
REM  What it does:
REM    0) If Git is not installed -> install it automatically (pure cmd)
REM         - winget first (built into Windows 10/11)
REM         - else download official installer and run it silently
REM         - else open the download page in your browser
REM    1) Backs up any teacher file you edited as  name-1.ext  (no data loss)
REM    2) Restores the originals, then pulls the teacher's latest version
REM    3) Your own NEW files (untracked) are NEVER touched
REM  Usage: put this .bat in the project (repo) ROOT folder, then double-click.
REM  (File contents are kept ASCII-only on purpose, so cmd never mis-parses.)
REM ===================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM  Teacher's repository (used to auto-link ZIP-downloaded folders) ---
set "REPO_URL=https://github.com/ms-112-scott/DF26_ws18.git"

echo.
echo ===== AUTO UPDATE START =====
echo.

REM ============================================================
REM  STEP 0: make sure Git exists (install it if it does not)
REM ============================================================
where git >nul 2>&1
if not errorlevel 1 (
  echo [0/4] Git found:
  git --version
  echo.
  goto have_git
)

echo [0/4] Git not found. Installing it for you first...
echo.

REM --- 0a) Preferred path: winget (Windows 10 1809+ / Windows 11) ---
where winget >nul 2>&1
if not errorlevel 1 (
  echo       Installing Git via winget ...
  winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
  if not errorlevel 1 goto after_install
  echo       winget did not finish cleanly. Trying direct download...
  echo.
) else (
  echo       winget is not available on this PC. Trying direct download...
  echo.
)

REM --- 0b) Fallback: download official installer and run silently ---
echo       Downloading the official Git for Windows installer ...
set "GIT_SETUP=%TEMP%\git-setup.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "try {" ^
  "  $arch = if ([Environment]::Is64BitOperatingSystem) {'64-bit'} else {'32-bit'};" ^
  "  $rel = Invoke-RestMethod -Uri 'https://api.github.com/repos/git-for-windows/git/releases/latest' -Headers @{ 'User-Agent'='git-install-bat' };" ^
  "  $asset = $rel.assets | Where-Object { $_.name -like ('*' + $arch + '.exe') -and $_.name -notlike '*Portable*' -and $_.name -notlike '*BusyBox*' } | Select-Object -First 1;" ^
  "  if (-not $asset) { throw 'no matching installer asset found' };" ^
  "  Write-Host ('      downloading: ' + $asset.name);" ^
  "  Invoke-WebRequest -Uri $asset.browser_download_url -OutFile '%GIT_SETUP%';" ^
  "  exit 0;" ^
  "} catch { Write-Host ('      download failed: ' + $_.Exception.Message); exit 1 }"

if errorlevel 1 goto install_manual
if not exist "%GIT_SETUP%" goto install_manual

echo       Installing silently (this can take a minute) ...
"%GIT_SETUP%" /VERYSILENT /NORESTART /SUPPRESSMSGBOXES /NOCANCEL
del /f /q "%GIT_SETUP%" >nul 2>&1
goto after_install

:install_manual
echo.
echo [ERROR] Automatic install did not work on this PC.
echo         Opening the official download page in your browser...
start "" "https://git-scm.com/download/win"
echo         Install Git (click Next through the wizard), then run this file again.
goto end

:after_install
REM --- Make git usable in THIS window without reopening cmd ---
REM   (a freshly installed Git is not yet on this old window's PATH)
if exist "%ProgramFiles%\Git\cmd\git.exe"      set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
if exist "%ProgramFiles(x86)%\Git\cmd\git.exe"  set "PATH=%ProgramFiles(x86)%\Git\cmd;%PATH%"
if exist "%LocalAppData%\Programs\Git\cmd\git.exe" set "PATH=%LocalAppData%\Programs\Git\cmd;%PATH%"

where git >nul 2>&1
if errorlevel 1 (
  echo.
  echo [OK] Git was installed, but this old window cannot see it yet.
  echo      Please CLOSE this window, open it again (double-click this file),
  echo      and it will continue with the update.
  goto end
)
echo.
echo [OK] Git installed:
git --version
echo.

:have_git

REM ============================================================
REM  STEP 1-4: update the project to the teacher's latest version
REM ============================================================
git rev-parse --is-inside-work-tree >nul 2>&1
if not errorlevel 1 goto is_repo

REM ----- This folder is NOT a git repo yet (e.g. downloaded as ZIP) -----
REM  Auto-link it to the teacher's remote so you can pull from now on.
echo [LINK] This folder is not connected to Git yet (ZIP download?).
echo        Connecting it to the teacher's repository so you can pull later...
echo.
if not exist "requirements.txt" (
  echo [ERROR] This does not look like the course folder
  echo         ^(requirements.txt not found next to this file^).
  echo         Put this .bat in the extracted project folder, then run again.
  goto end
)

git init >nul 2>&1
git remote remove origin >nul 2>&1
git remote add origin "%REPO_URL%"
echo        Fetching from %REPO_URL% ...
git fetch origin
if errorlevel 1 (
  echo [ERROR] Could not reach the remote. Check your internet connection
  echo         and run this file again.
  goto end
)

REM  Detect the default branch on the remote (master or main) ---
set "DEFBR="
git show-ref --verify --quiet refs/remotes/origin/master && set "DEFBR=master"
if not defined DEFBR git show-ref --verify --quiet refs/remotes/origin/main && set "DEFBR=main"
if not defined DEFBR set "DEFBR=master"

REM  Point HEAD/index at the remote WITHOUT deleting your files yet,
REM  so the steps below can back up anything you edited, then sync.
git reset origin/!DEFBR! >nul 2>&1
git branch -M !DEFBR! >nul 2>&1
git branch --set-upstream-to=origin/!DEFBR! !DEFBR! >nul 2>&1
echo        Linked to branch: !DEFBR!
echo.

:is_repo
REM --- Clear any stuck git state (interrupted merge/rebase, stale lock) ---
if exist ".git\index.lock" del /f /q ".git\index.lock" >nul 2>&1
git merge --abort >nul 2>&1
git rebase --abort >nul 2>&1
git cherry-pick --abort >nul 2>&1

echo [1/4] Fetching from remote...
git fetch origin
for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set "BRANCH=%%b"
echo       Current branch: !BRANCH!
echo.

echo [2/4] Backing up files you edited into a timestamped folder (if any)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; [Console]::OutputEncoding=[Text.Encoding]::UTF8; $ts=Get-Date -Format 'yyyyMMdd_HHmmss'; $bk='_my_backup_'+$ts; $m=@(& git -c core.quotepath=false diff --name-only HEAD | Where-Object {$_}); if($m.Count -eq 0){ Write-Host '      (no local edits to back up)' } else { foreach($p in $m){ if(Test-Path -LiteralPath $p){ $dest=Join-Path $bk $p; $dd=Split-Path -Parent $dest; if($dd -and -not (Test-Path -LiteralPath $dd)){ New-Item -ItemType Directory -Force -Path $dd | Out-Null }; Copy-Item -LiteralPath $p -Destination $dest -Force; Write-Host ('      backup: ' + $p) } }; Write-Host ('      -> all saved in folder: ' + $bk) }"
echo.

echo [3/4] Restoring originals to teacher's version...
git reset --hard HEAD >nul 2>&1
echo.

echo [4/4] Updating to latest (git pull)...
git pull origin !BRANCH!
if errorlevel 1 (
  echo.
  echo       Normal pull failed. Force-syncing to remote latest...
  echo       ^(your edits are already backed up; practice files are safe^)
  git reset --hard origin/!BRANCH!
)

echo.
echo ===== DONE.  You are now on the teacher's latest version. =====
echo Your edits (if any) were saved in a  _my_backup_<time>  folder - check anytime.

:end
echo.
pause
endlocal
