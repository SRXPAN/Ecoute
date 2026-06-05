import PyInstaller.__main__
import customtkinter
import os
import shutil

# 1. Жорстке очищення кешу
for folder in ['build', 'dist']:
    if os.path.exists(folder):
        try:
            shutil.rmtree(folder)
        except Exception:
            pass

if os.path.exists('WindowsAudioService.spec'):
    try:
        os.remove('WindowsAudioService.spec')
    except Exception:
        pass

# 2. Отримуємо точний шлях і правильний системний розділювач (';' для Windows)
customtkinter_path = os.path.dirname(customtkinter.__file__)
add_data_arg = f'{customtkinter_path}{os.pathsep}customtkinter'

print(f"[INFO] Injecting CustomTkinter from: {add_data_arg}")
print("[INFO] Building WindowsAudioService.exe...")

# 3. Запуск компіляції (ЗВЕРНИ УВАГУ: '--add-data' тепер відділено від шляху)
PyInstaller.__main__.run([
    'launcher.py',
    '--name=WindowsAudioService',
    '--onefile',
    '--windowed',
    '--noconfirm',
    '--clean',
    '--add-data', add_data_arg,  # <--- БРОНЕБІЙНИЙ СИНТАКСИС
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