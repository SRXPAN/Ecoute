import PyInstaller.__main__
import customtkinter
import os
import shutil

# Clean previous builds to prevent cached .spec file issues
for folder in ['build', 'dist']:
    if os.path.exists(folder):
        shutil.rmtree(folder)
if os.path.exists('WindowsAudioService.spec'):
    os.remove('WindowsAudioService.spec')

# Find customtkinter absolute path
customtkinter_path = os.path.dirname(customtkinter.__file__)

print("[INFO] Building WindowsAudioService.exe...")
PyInstaller.__main__.run([
    'launcher.py',
    '--name=WindowsAudioService',
    '--onefile',
    '--windowed',
    '--noconfirm',
    '--clean',
    f'--add-data={customtkinter_path};customtkinter/',
    '--hidden-import=pyaudiowpatch',
    '--hidden-import=_portaudiowpatch',
    '--collect-all=pyaudiowpatch',
    '--hidden-import=groq',
    '--hidden-import=openai',
    '--hidden-import=dotenv',
    '--hidden-import=sounddevice',
    '--hidden-import=keyboard',
    '--hidden-import=main',
    '--hidden-import=AudioRecorder',
    '--hidden-import=AudioTranscriber',
    '--hidden-import=LLMClient',
    '--hidden-import=StealthOverlay'
])
print("\n[SUCCESS] Executable created in the 'dist' folder!")
