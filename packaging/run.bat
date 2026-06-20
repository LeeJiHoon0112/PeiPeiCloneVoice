@echo off
setlocal EnableExtensions
set "SCRIPT_DIR=%~dp0"
set "PYEXE=%SCRIPT_DIR%venv\Scripts\python.exe"

if not exist "%PYEXE%" (
  echo [ERROR] Not installed yet. Please run install.bat first.
  pause
  exit /b 1
)

echo Starting PeiPei Clone Voice ... (first run downloads the model + asks for license)
"%PYEXE%" "%SCRIPT_DIR%main.py"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo [ERROR] Application exited with code %RC%.
  pause
)
exit /b %RC%
