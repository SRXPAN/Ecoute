"""
PyInstaller Build Script for AI Interview Copilot
Single-file executable with no console window

Usage:
    python build.py

Output:
    dist/InterviewCopilot.exe - Single executable file
"""

import PyInstaller.__main__
import os
import sys
import shutil
from pathlib import Path

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"[INFO] Cleaning {dir_name}/")
            shutil.rmtree(dir_name)

    # Clean .spec files
    for spec_file in Path('.').glob('*.spec'):
        print(f"[INFO] Removing {spec_file}")
        spec_file.unlink()

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'customtkinter',
        'pyaudiowpatch',
        'groq',
        'google-generativeai',
        'python-dotenv',
        'sounddevice',
        'numpy',
        'wave'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_').replace('.', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("[ERROR] Missing required packages:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("\nInstall missing packages with:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    print("[INFO] All dependencies found")

def build_single_exe():
    """Build single-file executable with PyInstaller"""

    print("\n" + "="*60)
    print("  Building AI Interview Copilot (Single EXE)")
    print("="*60 + "\n")

    # Check dependencies
    check_dependencies()

    # Clean previous builds
    clean_build_dirs()

    print("\n[INFO] Starting PyInstaller build...")
    print("[INFO] This may take several minutes...\n")

    # PyInstaller command for single-file executable
    PyInstaller.__main__.run([
        'launcher.py',                          # Entry point
        '--name=InterviewCopilot',              # Executable name
        '--onefile',                            # Single file
        '--windowed',                           # No console window
        '--add-data=.env.example;.',            # Include .env.example

        # Hidden imports
        '--hidden-import=customtkinter',
        '--hidden-import=pyaudiowpatch',
        '--hidden-import=groq',
        '--hidden-import=google.generativeai',
        '--hidden-import=google.ai.generativelanguage',
        '--hidden-import=dotenv',
        '--hidden-import=sounddevice',
        '--hidden-import=numpy',
        '--hidden-import=wave',
        '--hidden-import=ctypes',
        '--hidden-import=threading',
        '--hidden-import=queue',
        '--hidden-import=main',
        '--hidden-import=AudioRecorder',
        '--hidden-import=AudioTranscriber',
        '--hidden-import=LLMClient',
        '--hidden-import=StealthOverlay',

        # Exclude unnecessary packages
        '--exclude-module=matplotlib',
        '--exclude-module=scipy',
        '--exclude-module=pandas',
        '--exclude-module=PIL',
        '--exclude-module=tkinter.test',
        '--exclude-module=unittest',
        '--exclude-module=test',

        # Optimization
        '--clean',
        '--noconfirm',
    ])

    print("\n" + "="*60)
    print("  Build Complete!")
    print("="*60)
    print("\nOutput: dist/InterviewCopilot.exe")
    print("\nIMPORTANT:")
    print("  1. FFmpeg must be installed on the target system")
    print("  2. Users need to configure API keys on first run")
    print("  3. Windows 10 (2004+) or Windows 11 required for stealth mode")
    print("\nTo distribute:")
    print("  - Share the dist/InterviewCopilot.exe file")
    print("  - Include README_COMPLETE.md for setup instructions")
    print("  - Users double-click InterviewCopilot.exe to launch")
    print()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Build AI Interview Copilot')
    parser.add_argument(
        '--clean-only',
        action='store_true',
        help='Only clean build directories without building'
    )

    args = parser.parse_args()

    if args.clean_only:
        clean_build_dirs()
        print("[INFO] Build directories cleaned")
    else:
        build_single_exe()
