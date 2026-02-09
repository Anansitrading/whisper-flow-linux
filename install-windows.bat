@echo off
REM WhisperFlow Windows Installer
echo === WhisperFlow Windows Installer ===
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo Found Python %PYVER%

REM Create venv
echo.
echo [1/4] Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment.
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo [2/4] Installing Python dependencies (this may take a few minutes)...
pip install --upgrade pip -q
pip install -r requirements.txt -q
if errorlevel 1 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)

REM Download Whisper model
echo [3/4] Downloading Whisper base.en model (~74MB)...
python -c "from faster_whisper import WhisperModel; print('Downloading model...', flush=True); model = WhisperModel('base.en', device='cpu', compute_type='int8'); print('Model ready!', flush=True)"

REM Create default config
echo [4/4] Creating default configuration...
python -c "from whisperflow.config import ensure_config_exists; ensure_config_exists()"

REM Create launcher script
echo @echo off > whisperflow-run.bat
echo call "%%~dp0venv\Scripts\activate.bat" >> whisperflow-run.bat
echo python -m whisperflow %%* >> whisperflow-run.bat

echo.
echo === Installation Complete ===
echo.
echo Usage:
echo   whisperflow-run.bat                  Start WhisperFlow
echo   whisperflow-run.bat --list-devices   Show audio devices
echo   whisperflow-run.bat --hotkey f10     Use F10 as hotkey
echo.
echo Config: %%APPDATA%%\WhisperFlow\config.yaml
echo Default hotkey: Ctrl+Shift (hold to record, release to type)
echo.
pause
