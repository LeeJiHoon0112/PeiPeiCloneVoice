@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"

rem Prefer this app's own venv (if install.bat was run), else reuse the Tool venv
set "PYEXE=%SCRIPT_DIR%venv\Scripts\python.exe"
if not exist "%PYEXE%" set "PYEXE=C:\Users\Admin\Desktop\Clone\Tool\venv\Scripts\python.exe"

if not exist "%PYEXE%" (
  echo [ERROR] Python environment not found.
  echo Please run install.bat first.
  pause
  exit /b 1
)

echo Starting PeiPei Clone Voice ... (loading model, please wait)
"%PYEXE%" "%SCRIPT_DIR%main.py"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo [ERROR] Application exited with code %RC%.
  pause
)
exit /b %RC%
