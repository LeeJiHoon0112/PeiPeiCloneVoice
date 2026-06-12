@echo off
setlocal EnableExtensions

rem ============================================================
rem  PeiPei Clone Voice - Reset GPU clock to default
rem  Undoes ep_xung_gpu.bat (removes the locked clock).
rem  Run as Administrator.
rem ============================================================

net session >nul 2>&1
if errorlevel 1 (
  echo [LOI] Hay chay bang quyen Administrator (chuot phai -^> Run as administrator).
  pause
  exit /b 1
)

where nvidia-smi >nul 2>nul
if errorlevel 1 ( echo [LOI] Khong tim thay nvidia-smi. & pause & exit /b 1 )

nvidia-smi -rgc
echo.
echo [OK] Da tra xung nhip GPU ve mac dinh.
pause
