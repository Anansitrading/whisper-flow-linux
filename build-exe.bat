@echo off
REM Build WhisperFlow Windows Executable
REM Requires: pip install pyinstaller
echo === Building WhisperFlow Windows Executable ===
echo.

REM Activate venv if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Install PyInstaller
echo [1/4] Installing PyInstaller...
pip install pyinstaller -q

REM Find the Whisper model cache
echo [2/4] Locating Whisper model...
set MODEL_DIR=%USERPROFILE%\.cache\huggingface\hub\models--Systran--faster-whisper-base.en
if not exist "%MODEL_DIR%" (
    echo Warning: Model not found at %MODEL_DIR%
    echo The model will be downloaded on first run.
    set MODEL_ARG=
) else (
    set MODEL_ARG=--add-data "%MODEL_DIR%;models/models--Systran--faster-whisper-base.en"
)

REM Find CTranslate2 DLLs
echo [3/4] Collecting dependencies...

REM Build the exe
echo [4/4] Building executable (this may take several minutes)...
pyinstaller ^
    --name WhisperFlow ^
    --onedir ^
    --windowed ^
    --icon NONE ^
    --hidden-import=faster_whisper ^
    --hidden-import=ctranslate2 ^
    --hidden-import=sounddevice ^
    --hidden-import=pystray ^
    --hidden-import=pynput ^
    --hidden-import=pynput.keyboard ^
    --hidden-import=pynput.keyboard._win32 ^
    --hidden-import=numpy ^
    --hidden-import=PIL ^
    --hidden-import=yaml ^
    --collect-all faster_whisper ^
    --collect-all ctranslate2 ^
    --collect-all sounddevice ^
    --copy-metadata faster_whisper ^
    %MODEL_ARG% ^
    --add-data "config.yaml;." ^
    whisperflow\__main__.py

if errorlevel 1 (
    echo.
    echo Build failed! Check errors above.
    pause
    exit /b 1
)

echo.
echo === Build Complete ===
echo.
echo Output: dist\WhisperFlow\WhisperFlow.exe
echo.
echo To distribute: zip the entire dist\WhisperFlow\ folder.
echo Your friend can run WhisperFlow.exe directly.
echo.
pause
