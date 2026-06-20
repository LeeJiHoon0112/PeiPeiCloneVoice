@echo off
setlocal EnableExtensions
rem ============================================================
rem  build_installer.bat - DEV ONLY. Dong release\ thanh Setup.exe.
rem  Chay SAU build.bat (can co thu muc release\).
rem  Yeu cau: da cai Inno Setup 6 (free: https://jrsoftware.org/isdl.php).
rem  Output: build\PeiPeiCloneVoice_Setup.exe
rem ============================================================
cd /d "%~dp0.."

if not exist "release\run.bat" (
  echo [LOI] Chua co thu muc release\. Hay chay build.bat truoc.
  pause & exit /b 1
)

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo [LOI] Khong tim thay Inno Setup 6 ^(ISCC.exe^).
  echo       Tai + cai mien phi tai: https://jrsoftware.org/isdl.php
  pause & exit /b 1
)

echo Dong installer bang Inno Setup...
"%ISCC%" "packaging\installer.iss"
if errorlevel 1 ( echo [LOI] Compile installer that bai. & pause & exit /b 1 )

echo.
echo XONG. File cai dat: build\PeiPeiCloneVoice_Setup.exe
echo Gui file Setup.exe nay cho khach (kem license key).
pause
