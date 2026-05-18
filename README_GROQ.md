# AI Interview Copilot - Groq-Powered Transcription

## Overview

This is a refactored version of Ecoute that uses **Groq's ultra-fast Whisper API** for real-time speech-to-text transcription. All OpenAI dependencies have been removed in favor of Groq's free, high-performance API.

## Quick Start (1-Click Launch)

Simply double-click `start.bat` to launch the application!

## What's New

### ✅ Groq API Integration
- **Ultra-fast transcription** using Groq's `whisper-large-v3` model
- **Free API** with generous rate limits
- **Multi-language support** (English, Ukrainian, Polish, and more)
- **No local model downloads** - everything runs via API

### ✅ Removed Dependencies
- ❌ OpenAI API (`openai` package)
- ❌ Faster Whisper (`faster-whisper`)
- ❌ PyTorch (`torch`) - no longer needed
- ❌ CTranslate2 (`ctranslate2`)
- ❌ Local Whisper models

### ✅ Simplified Architecture
- Single transcription backend (Groq only)
- No `--api` flag needed anymore
- Lightweight dependencies
- Faster startup time

## Setup Instructions

### 1. Get Your Groq API Key

1. Visit [https://console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (you'll need it in the launcher)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Launch the Application

**Option 1: One-Click (Recommended)**
```
Double-click start.bat
```

**Option 2: Manual**
```bash
python launcher.py
```

## Configuration Launcher

When you launch the application, a configuration window appears:

### Audio Device Selection
- **Microphone Input**: Select your microphone from the dropdown
- **Speaker Output**: Select your speaker/virtual cable for capturing interviewer audio
- Default devices are automatically marked

### API Configuration
- **Provider**: Groq (Whisper) - pre-selected
- **API Key**: Enter your Groq API key (masked for security)
- Settings are saved to `.env` file

### Interview Context
- Paste your resume and/or job description
- Saved to `temp_context.txt` for AI assistance
- Automatically loaded in future sessions

### Start Button
Click the green **START** button to launch the transcription interface.

## How It Works

```
Launcher (launcher.py)
    ↓
Saves config to .env
    ↓
Launches main.py
    ↓
Captures audio from mic + speakers
    ↓
Sends audio chunks to Groq API
    ↓
Displays real-time transcription
```

## Files Structure

```
├── launcher.py              # Configuration GUI (entry point)
├── start.bat               # One-click launcher
├── main.py                 # Main transcription UI
├── AudioRecorder.py        # Audio capture logic
├── AudioTranscriber.py     # Transcription orchestration
├── TranscriberModels.py    # Groq API integration
├── requirements.txt        # Python dependencies
├── .env                    # API keys & config (auto-generated)
├── .env.example            # Template for .env
└── temp_context.txt        # Interview context (auto-generated)
```

## Requirements

- Python >=3.8.0
- FFmpeg (for audio processing)
- Windows OS (tested on Windows 11)
- Groq API key (free at console.groq.com)

## Dependencies

```
numpy
Wave
customtkinter
PyAudioWPatch
python-dotenv
sounddevice
groq
```

## Troubleshooting

### "GROQ_API_KEY not found in environment variables"
- Make sure you entered your API key in the launcher
- Check that `.env` file exists and contains `GROQ_API_KEY=your_key`

### "FFmpeg not found"
Install FFmpeg using Chocolatey:
```powershell
choco install ffmpeg
```

### No audio devices showing up
- Check Windows sound settings
- Ensure microphone and speakers are connected
- Restart the launcher

### Transcription is slow or failing
- Check your internet connection (Groq API requires internet)
- Verify your API key is valid
- Check Groq API status at [status.groq.com](https://status.groq.com)

## API Rate Limits

Groq offers generous free tier limits:
- **Requests per minute**: 30
- **Requests per day**: 14,400
- **Tokens per minute**: 20,000

For most interview scenarios, this is more than sufficient.

## Language Support

The `whisper-large-v3` model supports 99+ languages including:
- English
- Ukrainian
- Polish
- Spanish
- French
- German
- And many more...

To change the language, edit `TranscriberModels.py` line 19:
```python
language="en"  # Change to "uk" for Ukrainian, "pl" for Polish, etc.
```

## Performance

Groq's Whisper API is **significantly faster** than:
- OpenAI's Whisper API (5-10x faster)
- Local Whisper models (no GPU required)
- Faster-Whisper (no local model loading)

Typical transcription latency: **200-500ms**

## Credits

Based on the original [Ecoute](https://github.com/SevaSk/ecoute) project by SevaSk.

Refactored to use Groq API for ultra-fast, free transcription.

## License

Same as original Ecoute project.
