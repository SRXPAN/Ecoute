# 🚀 Deployment Guide - AI Interview Copilot

## Overview

This guide covers building, packaging, and deploying the AI Interview Copilot application for production use.

---

## 📦 Build Methods

### Method 1: Automated Setup Script (Recommended for Development)

The `run.bat` script automatically sets up a virtual environment and runs the application.

**Features:**
- ✅ Creates Python virtual environment
- ✅ Installs all dependencies
- ✅ Checks for FFmpeg
- ✅ Launches the application
- ✅ No manual setup required

**Usage:**
```bash
# Simply double-click or run:
run.bat
```

**What it does:**
1. Checks Python installation
2. Checks FFmpeg installation
3. Creates `venv/` directory if not exists
4. Activates virtual environment
5. Installs dependencies from `requirements.txt`
6. Launches `launcher.py`
7. Deactivates venv on exit

**First-time setup:** ~2-3 minutes (dependency installation)  
**Subsequent runs:** ~5 seconds

---

### Method 2: PyInstaller Build (Recommended for Distribution)

Build a standalone executable that doesn't require Python installation.

**Prerequisites:**
```bash
pip install pyinstaller
```

**Build Commands:**

**Option A: Directory Build (Recommended)**
```bash
python build.py
```

Output: `dist/InterviewCopilot/` folder with all files

**Option B: Single-File Build**
```bash
python build.py --onefile
```

Output: `dist/InterviewCopilot.exe` single executable

**Clean Build Directories:**
```bash
python build.py --clean-only
```

---

## 🏗️ Build Process Details

### Directory Structure After Build

```
dist/
└── InterviewCopilot/
    ├── InterviewCopilot.exe       # Main executable
    ├── _internal/                  # Python runtime and dependencies
    │   ├── customtkinter/
    │   ├── groq/
    │   ├── google/
    │   └── ... (other dependencies)
    ├── .env.example                # Environment template
    └── README_COMPLETE.md          # User documentation
```

### What Gets Included

**Python Files:**
- `launcher.py` (entry point)
- `main.py`
- `LLMClient.py`
- `StealthOverlay.py`
- `AudioRecorder.py`
- `AudioTranscriber.py`
- `TranscriberModels.py`
- `custom_speech_recognition/` (entire module)

**Data Files:**
- `.env.example`
- `README_COMPLETE.md`

**Dependencies:**
- CustomTkinter
- PyAudioWPatch
- Groq SDK
- Google Generative AI SDK
- Python-dotenv
- Sounddevice
- Numpy
- Wave

**NOT Included (User Must Install):**
- FFmpeg (system dependency)
- API keys (user configuration)

---

## 📋 Build Configuration

### PyInstaller Spec File

The `build.py` script generates `InterviewCopilot.spec` with:

```python
# Hidden imports (packages PyInstaller might miss)
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
]

# Excluded packages (reduce size)
excludes = [
    'matplotlib',
    'scipy',
    'pandas',
    'PIL',
    'tkinter.test',
]

# Console window (set to False to hide)
console = True
```

### Customizing the Build

**Change Console Visibility:**
Edit `build.py` line in spec template:
```python
console=False,  # Hide console window
```

**Add Application Icon:**
1. Create `icon.ico` file
2. Edit spec template in `build.py`:
```python
icon='icon.ico',
```

**Add More Data Files:**
Edit spec template in `build.py`:
```python
datas = [
    ('.env.example', '.'),
    ('README_COMPLETE.md', '.'),
    ('icon.png', '.'),  # Add your file
],
```

---

## 📦 Distribution Package

### Creating Distribution Package

**Step 1: Build the application**
```bash
python build.py
```

**Step 2: Create distribution folder**
```bash
mkdir InterviewCopilot_v1.0.0
```

**Step 3: Copy files**
```bash
# Copy the built application
xcopy /E /I dist\InterviewCopilot InterviewCopilot_v1.0.0\

# Copy documentation
copy README_COMPLETE.md InterviewCopilot_v1.0.0\
copy STEALTH_OVERLAY_GUIDE.md InterviewCopilot_v1.0.0\
copy .env.example InterviewCopilot_v1.0.0\
```

**Step 4: Create installation guide**
Create `InterviewCopilot_v1.0.0\INSTALL.txt`:
```
AI Interview Copilot - Installation Guide

REQUIREMENTS:
1. Windows 10 (version 2004+) or Windows 11
2. FFmpeg (install from https://ffmpeg.org or use: choco install ffmpeg)
3. Groq API Key (free at console.groq.com)
4. Gemini API Key (free at aistudio.google.com/app/apikey)

INSTALLATION:
1. Extract this folder to any location
2. Install FFmpeg if not already installed
3. Double-click InterviewCopilot.exe
4. Enter your API keys in the launcher
5. Configure audio devices
6. Click START

FIRST RUN:
- The application will create a .env file with your settings
- Your interview context will be saved to temp_context.txt
- The stealth overlay will appear automatically

TROUBLESHOOTING:
- If FFmpeg error: Install FFmpeg and restart
- If API error: Check your API keys are valid
- If audio error: Check device permissions in Windows settings

For full documentation, see README_COMPLETE.md
```

**Step 5: Create ZIP archive**
```bash
# Using PowerShell
Compress-Archive -Path InterviewCopilot_v1.0.0 -DestinationPath InterviewCopilot_v1.0.0.zip

# Or use 7-Zip, WinRAR, etc.
```

---

## 🎯 Deployment Checklist

### Pre-Build Checklist

- [ ] All dependencies in `requirements.txt`
- [ ] PyInstaller installed
- [ ] Code tested and working
- [ ] Documentation up to date
- [ ] Version number updated
- [ ] `.env.example` file present

### Build Checklist

- [ ] Run `python build.py`
- [ ] Check for build errors
- [ ] Test executable in `dist/InterviewCopilot/`
- [ ] Verify all features work
- [ ] Test stealth overlay
- [ ] Test API connections

### Distribution Checklist

- [ ] Create distribution folder
- [ ] Copy all necessary files
- [ ] Include documentation
- [ ] Create INSTALL.txt
- [ ] Test on clean Windows machine
- [ ] Create ZIP archive
- [ ] Upload to distribution platform

---

## 🧪 Testing the Build

### Local Testing

**Test 1: Basic Launch**
```bash
cd dist\InterviewCopilot
InterviewCopilot.exe
```
✅ Launcher should appear

**Test 2: Configuration**
- Enter API keys
- Select audio devices
- Add context text
- Click START
✅ Main application should launch

**Test 3: Transcription**
- Speak into microphone
- Play audio through speakers
✅ Transcription should appear

**Test 4: AI Suggestions**
- Wait for interviewer question (>20 chars)
✅ AI suggestions should stream in

**Test 5: Stealth Overlay**
- Check overlay is visible
- Start screen sharing (Zoom/Teams)
✅ Overlay should be invisible to others

### Clean Machine Testing

**Test on a machine without:**
- Python installed
- Development tools
- Previous application versions

**Steps:**
1. Copy `dist/InterviewCopilot/` folder
2. Install FFmpeg only
3. Run `InterviewCopilot.exe`
4. Complete full workflow

✅ Should work without any Python installation

---

## 🐛 Common Build Issues

### Issue: "Module not found" error

**Cause:** PyInstaller missed a dependency

**Solution:** Add to `hiddenimports` in `build.py`:
```python
hiddenimports = [
    'missing_module_name',
]
```

### Issue: Large executable size

**Cause:** Including unnecessary packages

**Solution:** Add to `excludes` in `build.py`:
```python
excludes = [
    'large_package_name',
]
```

### Issue: Application crashes on startup

**Cause:** Missing data files or incorrect paths

**Solution:** 
1. Check console output for errors
2. Add missing files to `datas` in spec
3. Use relative paths in code

### Issue: FFmpeg not found

**Cause:** FFmpeg not in system PATH

**Solution:**
- User must install FFmpeg separately
- Include in INSTALL.txt instructions
- Or bundle FFmpeg binaries (increases size)

---

## 📊 Build Size Optimization

### Current Build Size

**Directory Build:** ~150-200 MB  
**Single-File Build:** ~180-230 MB

### Optimization Tips

**1. Exclude Unused Packages**
```python
excludes = [
    'matplotlib',
    'scipy',
    'pandas',
    'PIL',
    'tkinter.test',
    'unittest',
    'test',
]
```

**2. Use UPX Compression**
```python
upx=True,
upx_exclude=[],
```

**3. Remove Debug Symbols**
```python
strip=True,
```

**4. Optimize Python Bytecode**
```bash
python -OO build.py
```

---

## 🔄 Update Process

### Releasing Updates

**Version Numbering:** `MAJOR.MINOR.PATCH`
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

**Update Steps:**

1. **Update version in code**
   - Edit `launcher.py` title
   - Update documentation

2. **Test thoroughly**
   - All features working
   - No regressions
   - Clean machine test

3. **Build new version**
   ```bash
   python build.py
   ```

4. **Create changelog**
   ```
   Version 1.1.0 (2026-05-18)
   - Added feature X
   - Fixed bug Y
   - Improved performance Z
   ```

5. **Package and distribute**
   ```bash
   # Create versioned package
   mkdir InterviewCopilot_v1.1.0
   # ... copy files ...
   Compress-Archive -Path InterviewCopilot_v1.1.0 -DestinationPath InterviewCopilot_v1.1.0.zip
   ```

---

## 🌐 Distribution Platforms

### GitHub Releases

1. Create new release
2. Upload ZIP file
3. Add changelog
4. Tag version (v1.0.0)

### Direct Download

1. Host ZIP on web server
2. Provide download link
3. Include SHA256 checksum

### Microsoft Store (Future)

Requirements:
- MSIX package
- Developer account
- Code signing certificate

---

## 🔐 Code Signing (Optional)

### Why Sign?

- ✅ Prevents "Unknown Publisher" warnings
- ✅ Builds user trust
- ✅ Required for some distribution platforms

### How to Sign

**Get Certificate:**
- Purchase from CA (DigiCert, Sectigo, etc.)
- Or use self-signed for testing

**Sign Executable:**
```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\InterviewCopilot\InterviewCopilot.exe
```

---

## 📝 License & Legal

### Include in Distribution

- LICENSE file
- THIRD_PARTY_LICENSES (for dependencies)
- Privacy policy (if collecting data)
- Terms of use

### Open Source Compliance

If using open source dependencies:
- Include their licenses
- Comply with license terms
- Attribute original authors

---

## 🎓 Best Practices

### Development

- ✅ Use version control (Git)
- ✅ Tag releases
- ✅ Maintain changelog
- ✅ Test on multiple machines
- ✅ Document breaking changes

### Distribution

- ✅ Provide clear installation instructions
- ✅ Include troubleshooting guide
- ✅ Offer support channel
- ✅ Keep documentation updated
- ✅ Respond to user feedback

### Security

- ✅ Never include API keys in build
- ✅ Use secure update mechanism
- ✅ Validate user input
- ✅ Handle errors gracefully
- ✅ Log security events

---

## 📞 Support

For build issues:
1. Check console output for errors
2. Review PyInstaller documentation
3. Test on clean machine
4. Open GitHub issue with details

---

**Last Updated:** 2026-05-18  
**Build System Version:** 1.0.0  
**PyInstaller Version:** 6.0+

---

## Quick Reference

```bash
# Development run
run.bat

# Build for distribution
python build.py

# Build single file
python build.py --onefile

# Clean build directories
python build.py --clean-only

# Test build
cd dist\InterviewCopilot
InterviewCopilot.exe
```

---

**Ready to deploy!** 🚀
