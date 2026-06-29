@echo off
REM ===================================================================
REM  Auto-update tool for students  (clone / pull workflow)
REM  What it does:
REM    1) Backs up any teacher file you edited as  name-1.ext  (no data loss)
REM    2) Restores the originals, then pulls the teacher's latest version
REM    3) Your own NEW files (untracked) are NEVER touched
REM  Usage: put this .bat in the project (repo) ROOT folder, then double-click.
REM  (File contents are kept ASCII-only on purpose, so cmd never mis-parses.)
REM ===================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ===== AUTO UPDATE START =====
echo.

where git >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Git not found. Please install Git first: https://git-scm.com
  goto end
)

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo [ERROR] This folder is not a git project.
  echo         Put this file inside the cloned project folder, then run again.
  goto end
)

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

echo [2/4] Backing up files you edited (if any)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; [Console]::OutputEncoding=[Text.Encoding]::UTF8; $m=@(& git -c core.quotepath=false diff --name-only HEAD | Where-Object {$_}); if($m.Count -eq 0){ Write-Host '      (no local edits to back up)' } else { foreach($p in $m){ if(Test-Path -LiteralPath $p){ $d=Split-Path -Parent $p; $b=[IO.Path]::GetFileNameWithoutExtension($p); $e=[IO.Path]::GetExtension($p); $n=1; do { $name=('{0}-{1}{2}' -f $b,$n,$e); if([string]::IsNullOrEmpty($d)){ $c=$name } else { $c=Join-Path $d $name }; $n++ } while(Test-Path -LiteralPath $c); Copy-Item -LiteralPath $p -Destination $c -Force; Write-Host ('      backup: ' + $p + '  ->  ' + (Split-Path -Leaf $c)) } } }"
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
echo Your edits (if any) were saved as  name-1.ext  - check them anytime.

:end
echo.
pause
endlocal
