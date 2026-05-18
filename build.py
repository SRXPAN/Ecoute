"""
PyInstaller Build Script for AI Interview Copilot

This script creates a standalone executable bundle of the application.

Usage:
    python build.py

Output:
    dist/InterviewCopilot/  - Portable directory with all files
    dist/InterviewCopilot.exe - Main executable (if --onefile is used)
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
            __import__(package.replace('-', '_'))
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

def create_spec_file():
    """Create PyInstaller spec file with custom configuration"""

    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all data files
datas = [
    ('.env.example', '.'),
    ('README_COMPLETE.md', '.'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'customtkinter',
    'pyaudiowpatch',
    'groq',
    'google.generativeai',
    'google.ai.generativelanguage',
    'dotenv',
    'sounddevice',
    'numpy',
    'wave',
    'ctypes',
    'threading',
    'queue',
    'tempfile',
    'io',
    'datetime',
    'heapq',
]

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'tkinter.test',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='InterviewCopilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to False to hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='InterviewCopilot',
)
"""

    with open('InterviewCopilot.spec', 'w') as f:
        f.write(spec_content)

    print("[INFO] Created InterviewCopilot.spec")

def build_application():
    """Build the application using PyInstaller"""

    print("\n" + "="*60)
    print("  Building AI Interview Copilot")
    print("="*60 + "\n")

    # Check dependencies
    check_dependencies()

    # Clean previous builds
    clean_build_dirs()

    # Create spec file
    create_spec_file()

    # Build with PyInstaller
    print("\n[INFO] Starting PyInstaller build...")
    print("[INFO] This may take several minutes...\n")

    PyInstaller.__main__.run([
        'InterviewCopilot.spec',
        '--clean',
        '--noconfirm',
    ])

    print("\n" + "="*60)
    print("  Build Complete!")
    print("="*60)
    print("\nOutput directory: dist/InterviewCopilot/")
    print("Executable: dist/InterviewCopilot/InterviewCopilot.exe")
    print("\nIMPORTANT:")
    print("  1. FFmpeg must be installed on the target system")
    print("  2. Users need to configure API keys on first run")
    print("  3. Windows 10 (2004+) or Windows 11 required for stealth mode")
    print("\nTo distribute:")
    print("  - Zip the entire dist/InterviewCopilot/ folder")
    print("  - Include README_COMPLETE.md for setup instructions")
    print("  - Users run InterviewCopilot.exe to launch")
    print()

def create_onefile_build():
    """Create a single-file executable (larger file, slower startup)"""

    print("\n[INFO] Creating single-file executable...")

    PyInstaller.__main__.run([
        'launcher.py',
        '--name=InterviewCopilot',
        '--onefile',
        '--windowed',  # No console window
        '--add-data=.env.example;.',
        '--hidden-import=customtkinter',
        '--hidden-import=pyaudiowpatch',
        '--hidden-import=groq',
        '--hidden-import=google.generativeai',
        '--hidden-import=dotenv',
        '--hidden-import=sounddevice',
        '--clean',
        '--noconfirm',
    ])

    print("\n[INFO] Single-file build complete!")
    print("Output: dist/InterviewCopilot.exe")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Build AI Interview Copilot')
    parser.add_argument(
        '--onefile',
        action='store_true',
        help='Create single-file executable (slower startup, easier distribution)'
    )
    parser.add_argument(
        '--clean-only',
        action='store_true',
        help='Only clean build directories without building'
    )

    args = parser.parse_args()

    if args.clean_only:
        clean_build_dirs()
        print("[INFO] Build directories cleaned")
    elif args.onefile:
        create_onefile_build()
    else:
        build_application()
