@echo off
cls
echo ====================================================
echo            AI Interview Copilot Manager
echo ====================================================
echo [1] Run Application (Python Development Mode)
echo [2] Build Standalone Executable (PyInstaller EXE)
echo [3] Exit
echo ====================================================
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto RUN_DEV
if "%choice%"=="2" goto BUILD_EXE
if "%choice%"=="3" exit

echo Invalid choice. Please try again.
pause
goto :eof

:RUN_DEV
cls
echo ====================================================
echo         Running in Development Mode...
echo ====================================================
echo.
echo Checking virtual environment...

if not exist ".venv" (
    echo Virtual environment not found. Creating...
    python -m venv .venv
    call .venv\Scripts\activate
    echo Installing dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

echo.
echo Starting AI Interview Copilot...
python launcher.py

pause
goto :eof

:BUILD_EXE
cls
echo ====================================================
echo       Building Standalone Executable...
echo ====================================================
echo.
echo Setting up Virtual Environment...

if not exist ".venv" (
    python -m venv .venv
)

call .venv\Scripts\activate

echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Compiling Executable...
pyinstaller --name=InterviewCopilot --onefile --windowed --noconfirm --clean --hidden-import=customtkinter --hidden-import=pyaudiowpatch --hidden-import=groq --hidden-import=google.generativeai --hidden-import=google.ai.generativelanguage --hidden-import=dotenv --hidden-import=sounddevice --hidden-import=main --hidden-import=AudioRecorder --hidden-import=AudioTranscriber --hidden-import=LLMClient --hidden-import=StealthOverlay launcher.py

echo.
echo =======================================
echo Build Complete! Executable is in \dist
echo =======================================
echo.
set /p run_app="Do you want to launch the application now? (Y/N): "
if /I "%run_app%"=="Y" start "" "dist\InterviewCopilot.exe"

pause
goto :eof
