# AI Interview Copilot - Configuration Launcher

## Quick Start (1-Click Launch)

Simply double-click `start.bat` to launch the application!

## What Happens

1. **Configuration Window Opens**: A GUI launcher appears with all settings
2. **Select Audio Devices**: Choose your microphone and speaker/virtual cable from dropdown menus
3. **Configure LLM**: Select Gemini as provider and enter your API key
4. **Add Context**: Paste your resume and/or job description in the text area
5. **Click START**: The launcher saves your settings and launches the main transcription application

## Features

### Audio Device Selection
- Automatically scans and lists all available microphones
- Automatically scans and lists all available speaker outputs (including virtual cables)
- Default devices are marked for easy identification
- Selections are saved to `.env` file

### LLM Configuration
- Provider selection (currently Gemini, with OpenAI/Claude planned)
- Secure API key input (masked characters)
- Credentials saved locally in `.env` file
- No need to re-enter on subsequent launches

### Interview Context
- Large scrollable text area for resume and job description
- Context saved to `temp_context.txt`
- Automatically loaded in future sessions
- Used by the AI to provide relevant interview assistance

## Files Created

- `.env` - Stores API keys and device indices (auto-generated)
- `temp_context.txt` - Stores interview context (auto-generated)
- `launcher.py` - The configuration GUI
- `start.bat` - One-click launcher script

## Manual Installation

If you haven't installed dependencies yet:

```bash
pip install -r requirements.txt
```

## Manual Launch

```bash
python launcher.py
```

## Requirements

- Python >=3.8.0
- FFmpeg (for audio processing)
- Windows OS
- All dependencies from `requirements.txt`

## New Dependencies Added

- `python-dotenv` - For .env file management
- `sounddevice` - For audio device enumeration
- `google-generativeai` - For Gemini API integration

## Architecture

```
start.bat → launcher.py (Config UI) → main.py (Transcription UI)
                ↓
            .env file (API keys, device indices)
            temp_context.txt (Interview context)
```

## Troubleshooting

**No audio devices showing up?**
- Make sure your microphone and speakers are connected
- Check Windows sound settings
- Restart the launcher

**API key not saving?**
- Check file permissions in the project directory
- Ensure `.env` file is not read-only

**Application won't start?**
- Verify FFmpeg is installed: `ffmpeg -version`
- Check all dependencies are installed: `pip install -r requirements.txt`
- Look for error messages in the console

## Next Steps

After configuration, the main application will:
- Transcribe your microphone input (You)
- Transcribe speaker output (Interviewer)
- Use the interview context to provide AI-powered assistance
- Display real-time transcriptions in the UI
