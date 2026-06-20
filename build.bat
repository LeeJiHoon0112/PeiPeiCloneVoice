@echo off
setlocal EnableExtensions
rem ============================================================
rem  build.bat  -  DEV ONLY (tac gia). KHONG giao file nay cho khach.
rem
rem  1) Bien dich toan bo app/ -> 1 file .pyd (ma may native, Nuitka, MIEN PHI)
rem     => khach KHONG doc/sua duoc code (gom ca doan kiem tra license).
rem  2) Gom Python NHUNG (embeddable 3.13) => khach KHOI CAI Python.
rem  3) Gom thu muc ban "release\": khach chi giai nen + chay run.bat.
rem
rem  Khach nhan: python\ + main.py + app.*.pyd + setup.bat + run.bat + requirements + huong dan.
rem  KHONG bao gio kem thu muc app\ (source).
rem ============================================================
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

rem --- Python co Nuitka (venv dev dung chung). Doi neu may khac. ---
set "PY=C:\Users\Admin\Desktop\Clone\Tool\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo [1/5] Kiem tra LICENSE_ENABLED (ban ban PHAI = True)...
"%PY%" -c "from app import config; import sys; sys.exit(0 if config.LICENSE_ENABLED else 1)"
if errorlevel 1 (
  echo [DUNG] LICENSE_ENABLED dang = False trong app\config.py. Doi True roi build lai.
  pause & exit /b 1
)

echo [2/5] Bien dich app\ -^> .pyd bang Nuitka (mien phi, vai phut)...
del /q build\app.*.pyd 2>nul
"%PY%" -m nuitka --module app --include-package=app --assume-yes-for-downloads --output-dir=build --remove-output
if errorlevel 1 ( echo [LOI] Nuitka build that bai. & pause & exit /b 1 )

echo [3/5] Chuan bi Python nhung (tai 1 lan, cache vao build\python_base)...
"%PY%" packaging\prep_python.py build\python_base
if errorlevel 1 ( echo [LOI] Khong chuan bi duoc Python nhung. & pause & exit /b 1 )

echo [4/5] Gom thu muc ban release\ ...
if exist release rmdir /s /q release
mkdir release
xcopy /e /i /q /y "build\python_base\python" "release\python" >nul
copy /y main.py release\ >nul
copy /y build\app.*.pyd release\ >nul
copy /y requirements.txt release\ >nul
copy /y packaging\setup.bat release\ >nul
copy /y packaging\run.bat release\ >nul
copy /y packaging\HUONG_DAN_KHACH.txt release\ >nul
if exist icon.ico copy /y icon.ico release\ >nul

echo [5/5] XONG. Thu muc ban: %SCRIPT_DIR%release\
echo   - Co: python\ (Python nhung) + main.py + app.*.pyd + setup.bat + run.bat + huong dan.
echo   - KHONG co thu muc app\ source (da bao ve).
echo.
echo   Khach: giai nen -^> chay run.bat (tu cai deps lan dau) -^> kich hoat key.
echo   Buoc tiep: nen "release\" thanh .zip de ban, hoac dong installer Inno Setup
echo   (xem packaging\README_BUILD.md).
pause
