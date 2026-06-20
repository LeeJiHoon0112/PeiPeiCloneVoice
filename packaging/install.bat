@echo off
setlocal EnableExtensions
rem ============================================================
rem  PeiPei Clone Voice - Installer (for customers)
rem
rem  Creates a local virtual environment (venv) and installs:
rem    - PyTorch + torchaudio (CUDA 12.8, ask before CPU fallback)
rem    - omnivoice + PyQt5 + audio libs (from requirements.txt)
rem
rem  REQUIRES: Python 3.13 (64-bit) installed and on PATH.
rem            (the app is compiled for 3.13; other versions will NOT work)
rem            Get it at https://www.python.org/downloads/release/python-3139/
rem            An NVIDIA GPU is strongly recommended.
rem ============================================================

set "SCRIPT_DIR=%~dp0"
set "VENV=%SCRIPT_DIR%venv"
set "REQ=%SCRIPT_DIR%requirements.txt"

rem --- If a local venv already exists, skip (use "install.bat force" to rebuild) ---
if exist "%VENV%\Scripts\python.exe" if not "%~1"=="force" (
  echo [OK] Already installed. Just run:  run.bat
  echo      ^(or "install.bat force" to reinstall^)
  pause
  exit /b 0
)

rem --- REQUIRE Python 3.13 (app is compiled for cp313) ---
set "PY="
where py >nul 2>nul && (
  py -3.13 -c "import sys" >nul 2>nul && set "PY=py -3.13"
)
if "%PY%"=="" (
  python --version 2>nul | findstr /C:"3.13" >nul && set "PY=python"
)
if "%PY%"=="" (
  echo ============================================================
  echo  [ERROR] Python 3.13 ^(64-bit^) was not found.
  echo.
  echo  This app needs EXACTLY Python 3.13. Please install it:
  echo    https://www.python.org/downloads/release/python-3139/
  echo  Tick "Add Python to PATH" during setup, then run install.bat again.
  echo ============================================================
  pause
  exit /b 1
)
echo Using Python: %PY%

echo.
echo [1/4] Creating virtual environment...
%PY% -m venv "%VENV%"
if errorlevel 1 ( echo [ERROR] Failed to create venv. & pause & exit /b 1 )

call "%VENV%\Scripts\activate.bat"
python -m pip install --upgrade pip

echo.
echo [2/4] Installing PyTorch + torchaudio (CUDA 12.8)...
echo     (GPU wheels are ~2.5GB - this can take a while; a stable network helps)
set "TORCH_OK="
pip install --index-url https://download.pytorch.org/whl/cu128 torch==2.8.0+cu128 torchaudio==2.8.0+cu128
if not errorlevel 1 ( set "TORCH_OK=1" ) else (
  echo [WARN] First attempt failed ^(often a network hiccup^). Retrying once...
  pip install --index-url https://download.pytorch.org/whl/cu128 torch==2.8.0+cu128 torchaudio==2.8.0+cu128
  if not errorlevel 1 set "TORCH_OK=1"
)
if not defined TORCH_OK (
  echo.
  echo ============================================================
  echo  [!] COULD NOT INSTALL THE GPU ^(CUDA^) VERSION OF PYTORCH.
  echo  On a machine WITH an NVIDIA GPU the CPU version is 20-50x slower.
  echo  Usual causes: slow/unstable internet ^(~2.5GB^) or old NVIDIA driver.
  echo  RECOMMENDED: fix network/driver and run install.bat again.
  echo ============================================================
  choice /C YN /N /M "Install the SLOW CPU version anyway? (Y/N) : "
  if errorlevel 2 ( echo Stopped. & pause & exit /b 1 )
  pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0+cpu torchaudio==2.8.0+cpu
  if errorlevel 1 ( echo [ERROR] Failed to install torch. & pause & exit /b 1 )
)

echo.
echo [3/4] Installing app dependencies...
pip install -r "%REQ%"
if errorlevel 1 ( echo [ERROR] Failed to install dependencies. & pause & exit /b 1 )
pip install --no-deps einx==0.4.3 torch-dct==0.1.6 vector-quantize-pytorch==1.29.1 torchtune==0.6.1 torchao==0.17.0
if errorlevel 1 ( echo [ERROR] Failed to install runtime extras. & pause & exit /b 1 )

echo.
echo [4/4] Verifying...
python -c "import torch, omnivoice, PyQt5, soundfile, torchao, pyloudnorm, requests, cryptography, app; print('OK - torch', torch.__version__, '| CUDA:', torch.cuda.is_available())"
if errorlevel 1 (
  echo [ERROR] Verification failed. The app .pyd may need Python 3.13 exactly.
  pause & exit /b 1
)

echo.
echo ============================================================
echo  DONE. Run the app with:  run.bat
echo  (First launch downloads the AI model ~4.7GB and asks for your license key.)
echo ============================================================
pause
