@echo off
setlocal EnableExtensions

rem ============================================================
rem  PeiPei Clone Voice - Update
rem  Pulls the latest code from GitHub (git pull).
rem  Your saved voices, model and venv are NOT touched.
rem ============================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

where git >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git is not installed.
  echo Install Git at https://git-scm.com/download/win  then run this again.
  pause
  exit /b 1
)

if not exist "%SCRIPT_DIR%.git" (
  echo [ERROR] This folder is not a git clone.
  echo To enable one-click updates, get the app with:
  echo     git clone ^<repo-url^>
  pause
  exit /b 1
)

echo Checking for updates...
git pull
if errorlevel 1 (
  echo.
  echo [WARN] Update failed. If you edited files locally, git may have conflicts.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo  Updated! If install.bat or requirements changed, you may
echo  want to run install.bat force once. Then run: run.bat
echo ============================================================
pause
exit /b 0
