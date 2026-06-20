@echo off
setlocal EnableExtensions
rem ============================================================
rem  PeiPei Clone Voice - START HERE (double-click this).
rem  Uses the bundled Python in .\python\ (no system Python needed).
rem  On the very first run it sets itself up automatically.
rem ============================================================
set "DIR=%~dp0"
set "PY=%DIR%python\python.exe"

if not exist "%PY%" (
  echo [ERROR] Bundled Python missing. Please re-extract the program folder.
  pause & exit /b 1
)

rem --- First run: install components automatically ---
if not exist "%DIR%.setup_done" (
  call "%DIR%setup.bat"
  if errorlevel 1 exit /b 1
)

echo Starting PeiPei Clone Voice ...
echo (First run also downloads the AI model ~4.7GB and asks for your license key.)
"%PY%" "%DIR%main.py"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo [ERROR] The program exited with code %RC%.
  pause
)
exit /b %RC%
