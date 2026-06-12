@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ============================================================
rem  PeiPei Clone Voice - Lock GPU clock high (fix slow generation)
rem
rem  WHY: On some PCs the GPU drops its clock to a power-saving
rem  level during voice generation (bursty load), making it 10-30x
rem  slower even though the GPU is strong. This locks the graphics
rem  clock near maximum so it stays fast.
rem
rem  MUST RUN AS ADMINISTRATOR (right-click -> Run as administrator).
rem  The lock lasts until reboot or until you run reset_xung_gpu.bat.
rem ============================================================

rem --- Tu xin quyen Admin (UAC) neu chua co, roi chay lai chinh no ---
net session >nul 2>&1
if errorlevel 1 (
  echo Dang xin quyen Administrator... (bam YES o hop thoai UAC)
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b 0
)

where nvidia-smi >nul 2>nul
if errorlevel 1 (
  echo [LOI] Khong tim thay nvidia-smi (driver NVIDIA?).
  pause
  exit /b 1
)

echo Dang doc xung nhip toi da cua GPU...
for /f "tokens=1" %%A in ('nvidia-smi --query-gpu^=clocks.max.sm --format^="csv,noheader,nounits"') do set "MAXCLK=%%A"

if "%MAXCLK%"=="" (
  echo [LOI] Khong doc duoc xung nhip toi da.
  pause
  exit /b 1
)

rem --- Lock floor at ~60%% of max, ceiling at max ---
set /a "FLOOR=%MAXCLK% * 60 / 100"
echo Xung toi da: %MAXCLK% MHz  -^>  se khoa trong khoang %FLOOR%-%MAXCLK% MHz

nvidia-smi -lgc %FLOOR%,%MAXCLK%
if errorlevel 1 (
  echo.
  echo [LOI] Khong khoa duoc xung (co the GPU/driver khong cho).
  echo Thu cap nhat driver NVIDIA moi nhat tai nvidia.com/Download.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo  [OK] Da khoa xung nhip GPU o muc cao.
echo  Bay gio MO APP (run.bat) va tao giong - se nhanh hon nhieu.
echo.
echo  Khoa nay het khi tat may. Muon go thu cong: chay reset_xung_gpu.bat
echo ============================================================
pause
