@echo off
setlocal EnableExtensions

rem ============================================================
rem  PeiPei Clone Voice - GPU Diagnostic 2
rem  Measures the GPU WHILE generating voice (clock, utilization,
rem  PCIe) to find why a strong GPU is still slow. Changes nothing.
rem ============================================================

set "SCRIPT_DIR=%~dp0"
set "PYEXE=%SCRIPT_DIR%venv\Scripts\python.exe"
if not exist "%PYEXE%" set "PYEXE=C:\Users\Admin\Desktop\Clone\Tool\venv\Scripts\python.exe"

if not exist "%PYEXE%" (
  echo [ERROR] Python environment not found. Run install.bat first.
  pause
  exit /b 1
)

echo Running diagnostic 2 (measures GPU during generation), please wait...
echo.
"%PYEXE%" "%SCRIPT_DIR%chan_doan2.py"

echo.
echo ============================================================
echo  Done. Please SCREENSHOT everything above and send it back.
echo ============================================================
pause
