@echo off
setlocal EnableExtensions

rem ============================================================
rem  PeiPei Clone Voice - Installer
rem
rem  Creates a local virtual environment (venv) and installs:
rem    - PyTorch + torchaudio (CUDA 12.8, fallback to CPU)
rem    - omnivoice + PyQt5 + audio libs (from requirements.txt)
rem
rem  Requires: Python 3.10-3.13 installed and on PATH
rem            (get it at https://www.python.org/downloads/)
rem            An NVIDIA GPU is strongly recommended.
rem ============================================================

set "SCRIPT_DIR=%~dp0"
set "VENV=%SCRIPT_DIR%venv"
set "REQ=%SCRIPT_DIR%requirements.txt"

rem --- If author's shared Tool venv exists, reuse it (skip install) ---
set "TOOL_VENV=C:\Users\Admin\Desktop\Clone\Tool\venv\Scripts\python.exe"
if exist "%TOOL_VENV%" if not "%~1"=="force" (
  echo [OK] Found an existing compatible environment. Nothing to install.
  echo Just run:  run.bat
  pause
  exit /b 0
)

rem --- If a local venv already exists, skip (use force to rebuild) ---
if exist "%VENV%\Scripts\python.exe" if not "%~1"=="force" (
  echo [OK] Local venv already exists. Nothing to install.
  echo Just run:  run.bat   ^(or "install.bat force" to rebuild^)
  pause
  exit /b 0
)

rem --- Find Python ---
set "PY="
where py >nul 2>nul && (
  py -3.13 -c "import sys" >nul 2>nul && set "PY=py -3.13"
)
if "%PY%"=="" ( where py  >nul 2>nul && set "PY=py" )
if "%PY%"=="" ( where python >nul 2>nul && set "PY=python" )
if "%PY%"=="" (
  echo [ERROR] Python not found.
  echo Please install Python 3.10-3.13 from https://www.python.org/downloads/
  echo Remember to tick "Add Python to PATH" during setup.
  pause
  exit /b 1
)
echo Using Python launcher: %PY%

echo.
echo [1/4] Creating virtual environment...
%PY% -m venv "%VENV%"
if errorlevel 1 ( echo [ERROR] Failed to create venv. & pause & exit /b 1 )

call "%VENV%\Scripts\activate.bat"
python -m pip install --upgrade pip

echo.
echo [2/4] Installing PyTorch + torchaudio (CUDA 12.8)...
pip install --index-url https://download.pytorch.org/whl/cu128 torch==2.8.0+cu128 torchaudio==2.8.0+cu128
if errorlevel 1 (
  echo CUDA wheels failed - falling back to CPU ^(will be SLOW^)...
  pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0+cpu torchaudio==2.8.0+cpu
  if errorlevel 1 ( echo [ERROR] Failed to install torch. & pause & exit /b 1 )
)

echo.
echo [3/4] Installing app dependencies...
pip install -r "%REQ%"
if errorlevel 1 ( echo [ERROR] Failed to install dependencies. & pause & exit /b 1 )

echo Installing audio-tokenizer runtime extras (no-deps)...
pip install --no-deps einx==0.4.3 torch-dct==0.1.6 vector-quantize-pytorch==1.29.1 torchtune==0.6.1 torchao==0.17.0
if errorlevel 1 ( echo [ERROR] Failed to install runtime extras. & pause & exit /b 1 )

echo.
echo [4/4] Verifying...
python -c "import torch, omnivoice, PyQt5, soundfile, torchao; print('OK - torch', torch.__version__, '| CUDA:', torch.cuda.is_available())"
if errorlevel 1 ( echo [ERROR] Verification failed. & pause & exit /b 1 )

echo.
echo ============================================================
echo  Done! Now run:  run.bat
echo  (First launch downloads the AI model ~4.7GB - one time.)
echo ============================================================
pause
exit /b 0
