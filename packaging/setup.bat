@echo off
setlocal EnableExtensions
rem ============================================================
rem  setup.bat - FIRST-TIME SETUP (runs automatically from run.bat).
rem  Installs PyTorch + libraries into the bundled Python.
rem  No system Python needed - everything uses .\python\ .
rem ============================================================
set "DIR=%~dp0"
set "PY=%DIR%python\python.exe"

if not exist "%PY%" (
  echo [ERROR] Bundled Python missing. Please re-extract the program folder.
  pause & exit /b 1
)

echo ============================================================
echo  FIRST-TIME SETUP - installing components (a few GB, one time).
echo  Please keep this window open and stay connected to the internet.
echo ============================================================
echo.
echo [1/3] Installing PyTorch (GPU / CUDA 12.8, ~2.5GB - can take a while)...
"%PY%" -m pip install --no-warn-script-location --index-url https://download.pytorch.org/whl/cu128 torch==2.8.0+cu128 torchaudio==2.8.0+cu128
if errorlevel 1 (
  echo [WARN] First attempt failed ^(often a network hiccup^). Retrying once...
  "%PY%" -m pip install --no-warn-script-location --index-url https://download.pytorch.org/whl/cu128 torch==2.8.0+cu128 torchaudio==2.8.0+cu128
  if errorlevel 1 (
    echo.
    echo [ERROR] Could not install PyTorch ^(GPU^). Usual causes:
    echo   - Slow/unstable internet while downloading ^(~2.5GB^)
    echo   - Old NVIDIA driver ^(update at nvidia.com/Download^)
    echo Fix the issue and just run the program again.
    pause & exit /b 1
  )
)

echo.
echo [2/3] Installing app libraries...
"%PY%" -m pip install --no-warn-script-location -r "%DIR%requirements.txt"
if errorlevel 1 ( echo [ERROR] Failed to install libraries. & pause & exit /b 1 )
"%PY%" -m pip install --no-warn-script-location --no-deps einx==0.4.3 torch-dct==0.1.6 vector-quantize-pytorch==1.29.1 torchtune==0.6.1 torchao==0.17.0
if errorlevel 1 ( echo [ERROR] Failed to install runtime extras. & pause & exit /b 1 )

echo.
echo [3/3] Verifying...
"%PY%" -c "import torch, app; print('OK - torch', torch.__version__, '| GPU:', torch.cuda.is_available())"
if errorlevel 1 ( echo [ERROR] Verification failed. & pause & exit /b 1 )

echo setup-done> "%DIR%.setup_done"
echo.
echo ============================================================
echo  Setup complete! The program will start now.
echo ============================================================
exit /b 0
