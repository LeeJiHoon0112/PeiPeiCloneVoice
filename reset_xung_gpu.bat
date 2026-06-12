@echo off
setlocal EnableExtensions

rem ============================================================
rem  PeiPei Clone Voice - Reset GPU clock to default
rem  Undoes ep_xung_gpu.bat (removes the locked clock).
rem  Run as Administrator.
rem ============================================================

net session >nul 2>&1
if errorlevel 1 (
  echo Dang xin quyen Administrator... (bam YES o hop thoai UAC)
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b 0
)

where nvidia-smi >nul 2>nul
if errorlevel 1 ( echo [LOI] Khong tim thay nvidia-smi. & pause & exit /b 1 )

nvidia-smi -rgc
echo.
echo [OK] Da tra xung nhip GPU ve mac dinh.
pause
