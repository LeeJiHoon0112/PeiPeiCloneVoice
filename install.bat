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
echo     (GPU wheels are ~2.5GB - this can take a while; a stable network helps)

rem --- Try the GPU (CUDA) wheels, with one automatic retry for flaky networks ---
set "TORCH_OK="
pip install --index-url https://download.pytorch.org/whl/cu128 torch==2.8.0+cu128 torchaudio==2.8.0+cu128
if not errorlevel 1 ( set "TORCH_OK=1" ) else (
  echo.
  echo [WARN] First attempt to install the GPU version failed ^(often just a network hiccup^).
  echo        Retrying once...
  echo.
  pip install --index-url https://download.pytorch.org/whl/cu128 torch==2.8.0+cu128 torchaudio==2.8.0+cu128
  if not errorlevel 1 set "TORCH_OK=1"
)

rem --- If GPU wheels still failed, DO NOT silently install CPU. Warn loudly + ask. ---
if not defined TORCH_OK (
  echo.
  echo ============================================================
  echo  [!] COULD NOT INSTALL THE GPU ^(CUDA^) VERSION OF PYTORCH.
  echo.
  echo  If this machine HAS an NVIDIA GPU, the CPU version will be
  echo  EXTREMELY SLOW ^(often 20-50x slower^). The usual causes are:
  echo    - Unstable / slow internet while downloading ^(~2.5GB^)
  echo    - Very old NVIDIA driver ^(update at nvidia.com/Download^)
  echo.
  echo  RECOMMENDED: fix the network/driver and run install.bat again.
  echo ============================================================
  echo.
  choice /C YN /N /M "Install the SLOW CPU version anyway? (Y = yes / N = stop) : "
  if errorlevel 2 (
    echo Stopped. No CPU version installed. Fix the issue and run install.bat again.
    pause
    exit /b 1
  )
  echo Installing CPU version ^(this will be SLOW^)...
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
python -c "import torch, omnivoice, PyQt5, soundfile, torchao, pyloudnorm, requests, cryptography; print('OK - torch', torch.__version__, '| CUDA:', torch.cuda.is_available())"
if errorlevel 1 ( echo [ERROR] Verification failed. & pause & exit /b 1 )

rem --- Warn LOUDLY if the final install ended up CPU-only (no GPU acceleration) ---
python -c "import torch, sys; sys.exit(0 if torch.cuda.is_available() else 1)"
if errorlevel 1 (
  echo.
  echo ============================================================
  echo  [!] WARNING: PyTorch cannot use your GPU ^(CUDA = False^).
  echo      Voice generation will be VERY SLOW ^(CPU mode^).
  echo.
  echo  Fix one of these, then run:  install.bat force
  echo    - You may have the CPU version of torch installed.
  echo    - Or your NVIDIA driver is too old ^(update it, need ^>= 525^).
  echo  Check with:
  echo    venv\Scripts\python.exe -c "import torch;print(torch.__version__,torch.cuda.is_available())"
  echo ============================================================
  echo.
)

echo.
echo ============================================================
echo  Done! Now run:  run.bat
echo  (First launch downloads the AI model ~4.7GB - one time.)
echo ============================================================
pause
exit /b 0
