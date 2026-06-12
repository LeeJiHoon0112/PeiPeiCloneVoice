@echo off
setlocal EnableExtensions

rem ============================================================
rem  PeiPei Clone Voice - GPU Diagnostic
rem  Double-click this file. It prints real numbers about your
rem  GPU and voice-generation speed, then waits so you can read
rem  / screenshot. It does NOT change or delete anything.
rem ============================================================

set "SCRIPT_DIR=%~dp0"

rem --- Pick the same Python the app uses (local venv, else Tool venv) ---
set "PYEXE=%SCRIPT_DIR%venv\Scripts\python.exe"
if not exist "%PYEXE%" set "PYEXE=C:\Users\Admin\Desktop\Clone\Tool\venv\Scripts\python.exe"

if not exist "%PYEXE%" (
  echo [ERROR] Python environment not found. Run install.bat first.
  pause
  exit /b 1
)

echo Running diagnostic, please wait (this loads the model)...
echo.
"%PYEXE%" "%SCRIPT_DIR%chan_doan.py"

echo.
echo ============================================================
echo  Done. Please SCREENSHOT everything above and send it back.
echo ============================================================
pause
