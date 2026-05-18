@echo off
SETLOCAL EnableDelayedExpansion

echo ========================================
echo   AI Interview Copilot - Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [INFO] Python found
python --version

REM Check if FFmpeg is installed
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] FFmpeg is not installed
    echo FFmpeg is required for audio processing
    echo.
    echo Install FFmpeg using Chocolatey:
    echo   choco install ffmpeg
    echo.
    echo Or download from: https://ffmpeg.org/download.html
    echo.
    pause
    exit /b 1
)

echo [INFO] FFmpeg found

REM Check if virtual environment exists
if not exist "venv" (
    echo.
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [INFO] Virtual environment created
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo [INFO] Checking dependencies...
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    echo This may take a few minutes...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [INFO] Dependencies installed successfully
) else (
    echo [INFO] Dependencies already installed
)

REM Launch the application
echo.
echo ========================================
echo   Launching AI Interview Copilot
echo ========================================
echo.

python launcher.py

REM Deactivate virtual environment on exit
call venv\Scripts\deactivate.bat

echo.
echo Application closed.
pause
