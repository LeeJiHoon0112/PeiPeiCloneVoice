@echo off
setlocal EnableExtensions
rem ============================================================
rem  build.bat  -  DEV ONLY (tac gia). KHONG giao file nay cho khach.
rem
rem  Bien dich toan bo code Python cua app/ thanh 1 file .pyd (ma may
rem  native) bang Nuitka (MIEN PHI) de khach KHONG doc/sua duoc code
rem  (gom ca doan kiem tra license). Sau do gom thu muc ban "release\".
rem
rem  Khach chi nhan: main.py + app.*.pyd + install.bat + run.bat + huong dan.
rem  KHONG bao gio kem thu muc app\ (source).
rem ============================================================
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

rem --- Python co Nuitka (venv dev dung chung). Doi neu may khac. ---
set "PY=C:\Users\Admin\Desktop\Clone\Tool\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo [1/4] Kiem tra LICENSE_ENABLED (ban ban PHAI = True)...
"%PY%" -c "from app import config; import sys; sys.exit(0 if config.LICENSE_ENABLED else 1)"
if errorlevel 1 (
  echo [DUNG] LICENSE_ENABLED dang = False trong app\config.py.
  echo        Doi thanh True roi build lai de ban.
  pause & exit /b 1
)

echo [2/4] Bien dich app\ -^> .pyd bang Nuitka (mien phi, vai phut)...
if exist build rmdir /s /q build
"%PY%" -m nuitka --module app --include-package=app --assume-yes-for-downloads --output-dir=build --remove-output
if errorlevel 1 ( echo [LOI] Nuitka build that bai. & pause & exit /b 1 )

echo [3/4] Gom thu muc ban release\ ...
if exist release rmdir /s /q release
mkdir release
copy /y main.py release\ >nul
copy /y build\app.*.pyd release\ >nul
copy /y requirements.txt release\ >nul
copy /y packaging\install.bat release\ >nul
copy /y packaging\run.bat release\ >nul
copy /y packaging\HUONG_DAN_KHACH.txt release\ >nul

echo [4/4] XONG. Thu muc ban: %SCRIPT_DIR%release\
echo   - Co: main.py + app.*.pyd (da bien dich) + install.bat + run.bat + huong dan.
echo   - KHONG co thu muc app\ source (da duoc bao ve).
echo.
echo   Buoc tiep: nen "release\" thanh .zip de gui khach, hoac dong installer
echo   bang Inno Setup (xem packaging\README_BUILD.md).
pause
