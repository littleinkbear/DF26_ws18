@echo off
REM ===================================================================
REM  One-click Git installer for students (Windows, pure cmd)
REM  What it does:
REM    1) If Git is already installed -> show version and stop
REM    2) Try winget (built into Windows 10/11)  -> install Git silently
REM    3) If winget is missing -> download official installer and run it
REM    4) If both fail -> open the download page in your browser
REM  Usage: just double-click this file.  No admin needed for winget.
REM  (File contents are kept ASCII-only on purpose, so cmd never mis-parses.)
REM ===================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ===== GIT INSTALL START =====
echo.

REM --- 1) Already installed? ---
where git >nul 2>&1
if not errorlevel 1 (
  echo [OK] Git is already installed:
  git --version
  echo.
  echo Nothing to do. You can close this window.
  goto end
)

echo [INFO] Git not found. Trying to install it for you...
echo.

REM --- 2) Preferred path: winget (Windows 10 1809+ / Windows 11) ---
where winget >nul 2>&1
if not errorlevel 1 (
  echo [1/2] Installing Git via winget ...
  winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
  if not errorlevel 1 goto verify
  echo.
  echo [WARN] winget install did not finish cleanly. Trying direct download...
  echo.
) else (
  echo [INFO] winget is not available on this PC. Trying direct download...
  echo.
)

REM --- 3) Fallback: download official installer and run silently ---
echo [2/2] Downloading the official Git for Windows installer ...
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

if errorlevel 1 goto manual
if not exist "%GIT_SETUP%" goto manual

echo       Installing silently (this can take a minute) ...
"%GIT_SETUP%" /VERYSILENT /NORESTART /SUPPRESSMSGBOXES /NOCANCEL
del /f /q "%GIT_SETUP%" >nul 2>&1

:verify
REM --- 4) Verify (refresh PATH for this window via a fresh shell) ---
echo.
echo [CHECK] Verifying installation ...
where git >nul 2>&1
if not errorlevel 1 (
  git --version
  goto done
)
REM PATH in this old window may be stale; try the default install location.
set "GITEXE=%ProgramFiles%\Git\cmd\git.exe"
if exist "%GITEXE%" (
  "%GITEXE%" --version
  goto done
)
echo [WARN] Could not confirm git in THIS window.
echo        Git may still be installed. Close this window, open a NEW cmd, and run:  git --version
goto end

:manual
echo.
echo [ERROR] Automatic install did not work on this PC.
echo         Opening the official download page in your browser...
start "" "https://git-scm.com/download/win"
echo         Download the 64-bit installer and click Next through the wizard.
goto end

:done
echo.
echo ===== DONE. Git is installed. =====
echo IMPORTANT: close this window and open a NEW cmd/PowerShell so PATH refreshes,
echo            then you can use:  git --version

:end
echo.
pause
endlocal
