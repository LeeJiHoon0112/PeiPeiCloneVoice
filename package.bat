@echo off
setlocal EnableExtensions

rem ============================================================
rem  Build a CLEAN shareable copy of the app (a ZIP file).
rem
rem  Excludes (NOT shared):
rem    - user_data\   (YOUR saved voices & outputs)  <-- private
rem    - venv\        (virtual environment, huge)
rem    - models\      (AI model ~4.7GB, friend re-downloads)
rem    - __pycache__, *.wav, *.log, context.md, test scripts
rem
rem  Output: a ZIP on your Desktop that you can send to a friend.
rem ============================================================

set "SRC=%~dp0"
set "STAGE=%TEMP%\PeiPeiCloneVoice_pkg"
set "OUTZIP=%USERPROFILE%\Desktop\PeiPeiCloneVoice_share.zip"

echo Building clean package (without your voices)...

rem --- fresh staging folder ---
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%"

rem --- copy everything EXCEPT private/heavy/temp items ---
robocopy "%SRC%." "%STAGE%" /E ^
  /XD venv models user_data __pycache__ .git .vscode .idea ^
  /XF *.wav *.log *.pyc context.md "_*.py" >nul
if errorlevel 8 (
  echo [ERROR] Copy failed.
  pause
  exit /b 1
)

rem --- zip it ---
if exist "%OUTZIP%" del /f /q "%OUTZIP%"
powershell -NoProfile -Command "Compress-Archive -Path '%STAGE%\*' -DestinationPath '%OUTZIP%' -Force"
if errorlevel 1 (
  echo [ERROR] Zip failed.
  pause
  exit /b 1
)

rmdir /s /q "%STAGE%"

echo.
echo ============================================================
echo  Done! Clean package created at:
echo    %OUTZIP%
echo.
echo  Send that ZIP to your friend. It does NOT contain your
echo  saved voices. They run install.bat then run.bat.
echo ============================================================
pause
exit /b 0
