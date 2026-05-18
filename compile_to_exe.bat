@echo off
echo Setting up Virtual Environment...
python -m venv .venv
call .venv\Scripts\activate

echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo Compiling Executable...
pyinstaller --name=InterviewCopilot --onefile --windowed --noconfirm --clean --hidden-import=customtkinter --hidden-import=pyaudiowpatch --hidden-import=groq --hidden-import=google.generativeai --hidden-import=google.ai.generativelanguage --hidden-import=dotenv --hidden-import=sounddevice --hidden-import=main --hidden-import=AudioRecorder --hidden-import=AudioTranscriber --hidden-import=LLMClient --hidden-import=StealthOverlay launcher.py

echo =======================================
echo Build Complete! Executable is in \dist
echo =======================================
set /p run_app="Do you want to launch the application now? (Y/N): "
if /I "%run_app%"=="Y" start "" "dist\InterviewCopilot.exe"
pause
