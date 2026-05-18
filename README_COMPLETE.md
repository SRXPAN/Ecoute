# 🎯 AI Interview Copilot - Complete Project

## 🌟 Overview

A production-ready AI-powered interview assistant with **stealth mode** that helps you succeed in technical interviews by providing real-time, context-aware suggestions that are **invisible to interviewers** during screen sharing.

### Key Features

✅ **Ultra-Fast Transcription** - Groq Whisper API (200-500ms latency)  
✅ **AI-Powered Suggestions** - Google Gemini with context awareness  
✅ **Stealth Mode Overlay** - Invisible in Zoom/Teams/Meet screen sharing  
✅ **Multilingual Support** - Auto-detects 99+ languages  
✅ **One-Click Setup** - GUI launcher with device selection  
✅ **Context-Aware** - Uses your resume and job description  

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Get API Keys (Both Free!)

**Groq API** (Transcription):
- Visit: [console.groq.com](https://console.groq.com)
- Sign up → Create API Key → Copy

**Gemini API** (AI Suggestions):
- Visit: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- Sign in → Create API Key → Copy

### Step 2: Install

```bash
# Clone repository
git clone <repo-url>
cd ecoute-main

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (Windows)
choco install ffmpeg
```

### Step 3: Launch

```bash
# One-click (recommended)
start.bat

# Or manual
python launcher.py
```

### Step 4: Configure

1. Select audio devices (auto-detected)
2. Enter both API keys
3. Paste your resume/job description
4. Click **START**

---

## 🎨 User Interface

### Main Application (1400x700)

```
┌─────────────────────────────────────────────────────────────┐
│                  AI Interview Copilot                        │
├──────────────────────────────┬──────────────────────────────┤
│  📝 Live Transcript          │  💡 AI Suggestions           │
│                              │                              │
│  You: [Your response...]     │  • Optimized DB queries 60%  │
│                              │  • Implemented Redis cache   │
│  Speaker: [Question...]      │  • Collaborated with DevOps  │
│                              │  • Result: 10x traffic spike │
│                              │                              │
│                              │                              │
│  [Clear All]                 │  [Toggle Stealth Overlay]    │
└──────────────────────────────┴──────────────────────────────┘
```

### Stealth Overlay (400x300)

```
┌─────────────────────────────────────┐
│ 💡 AI Assistant (Stealth Mode)   ✕ │  ← Draggable, Always on Top
├─────────────────────────────────────┤
│                                     │
│  • Optimized database queries 60%  │  ← Semi-transparent
│  • Implemented caching with Redis  │     (85% opacity)
│  • Collaborated with DevOps team   │
│  • Result: handled 10x traffic     │  ← Invisible in
│                                     │     screen sharing!
│                                     │
└─────────────────────────────────────┘
```

---

## 🕵️ Stealth Mode - The Secret Weapon

### What is Stealth Mode?

A frameless, always-on-top overlay window that displays AI suggestions on your screen but appears **completely black or invisible** to interviewers when you share your screen via Zoom, Teams, Meet, or OBS.

### How It Works

Uses Windows API `SetWindowDisplayAffinity` with `WDA_EXCLUDEFROMCAPTURE` flag:

```python
# Windows marks the window as excluded from screen capture
ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
```

### What You See vs What They See

| Your Screen | Interviewer's Screen |
|-------------|---------------------|
| ![Overlay with green text](visible) | ![Black box or nothing](invisible) |
| ✅ AI suggestions visible | ❌ Overlay excluded from capture |
| ✅ Can read bullet points | ❌ Sees black rectangle or nothing |
| ✅ Draggable and movable | ❌ Cannot see content |

### Tested Platforms

✅ **Zoom** - Overlay appears as black box  
✅ **Microsoft Teams** - Overlay invisible  
✅ **Google Meet** - Overlay invisible  
✅ **OBS Studio** - Overlay appears as black box  
✅ **Discord** - Overlay excluded from capture  

---

## 🤖 AI System Prompt

### Engineered for Interview Success

The AI is trained with a strict prompt that:

1. **Analyzes** interviewer questions in real-time
2. **Responds** with exactly 3-4 bullet points
3. **Uses** keywords only (no full sentences)
4. **References** your specific projects from context
5. **Matches** interviewer's language automatically

### Example Responses

**English Question:**
```
Interviewer: "Tell me about a time you optimized performance"

AI Suggestions:
• Optimized database queries - reduced latency 60%
• Implemented Redis caching layer
• Collaborated with DevOps on infrastructure
• Result: handled 10x traffic spike
```

**Polish Question:**
```
Interviewer: "Opowiedz o optymalizacji wydajności"

AI Suggestions:
• Optymalizacja zapytań SQL - redukcja 60%
• Implementacja cache Redis
• Współpraca z zespołem DevOps
• Rezultat: 10x więcej ruchu
```

**Ukrainian Question:**
```
Interviewer: "Розкажіть про оптимізацію продуктивності"

AI Suggestions:
• Оптимізація SQL запитів - зниження 60%
• Впровадження Redis кешування
• Співпраця з DevOps командою
• Результат: 10x більше трафіку
```

---

## 📊 Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    launcher.py (Entry)                       │
│  • Audio device scanning                                     │
│  • API key configuration                                     │
│  • Context input (resume/JD)                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    Saves to .env + temp_context.txt
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│  • Initializes audio recorders                               │
│  • Creates main UI (dual-pane)                               │
│  • Launches stealth overlay                                  │
│  • Manages LLM client                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                                             ↓
┌──────────────────────┐                  ┌──────────────────────┐
│  Audio Pipeline      │                  │  AI Pipeline         │
│                      │                  │                      │
│  Microphone          │                  │  LLMClient.py        │
│       ↓              │                  │       ↓              │
│  AudioRecorder       │                  │  Load Context        │
│       ↓              │                  │       ↓              │
│  Groq Whisper API    │                  │  Build Prompt        │
│       ↓              │                  │       ↓              │
│  Transcription       │──────────────────→  Gemini API          │
│                      │  (Speaker text)  │       ↓              │
└──────────────────────┘                  │  Stream Response     │
                                          └──────────────────────┘
                                                    ↓
                                          ┌──────────────────────┐
                                          │  StealthOverlay.py   │
                                          │  • Frameless window  │
                                          │  • Always on top     │
                                          │  • Screen exclusion  │
                                          │  • Real-time stream  │
                                          └──────────────────────┘
```

---

## 📁 Project Structure

```
ecoute-main/
├── launcher.py                 # 🚀 Entry point - Configuration GUI
├── start.bat                   # 🖱️ One-click launcher
├── main.py                     # 🎨 Main application with dual-pane UI
├── LLMClient.py                # 🤖 AI client manager (Gemini)
├── StealthOverlay.py           # 🕵️ Stealth mode overlay window
├── AudioRecorder.py            # 🎤 Audio capture (mic + speakers)
├── AudioTranscriber.py         # 📝 Transcription orchestration
├── TranscriberModels.py        # ⚡ Groq API integration
├── requirements.txt            # 📦 Python dependencies
├── .env                        # 🔑 API keys (auto-generated)
├── .env.example                # 📋 Environment template
├── temp_context.txt            # 📄 Interview context (auto-generated)
│
├── README.md                   # 📖 This file
├── README_AI_ASSISTANT.md      # 🤖 AI assistant guide
├── README_GROQ.md              # ⚡ Groq transcription guide
├── LAUNCHER_README.md          # 🚀 Launcher documentation
├── STEALTH_OVERLAY_GUIDE.md    # 🕵️ Stealth mode guide
├── IMPLEMENTATION_SUMMARY.md   # 📊 Technical summary
│
└── custom_speech_recognition/  # 🎙️ Speech recognition library
    ├── __init__.py
    ├── audio.py
    ├── exceptions.py
    └── recognizers/
        └── whisper.py
```

---

## 🎯 Use Cases

### 1. Technical Interviews
- **Problem**: Anxiety, forgetting key projects
- **Solution**: AI suggests relevant experience based on question
- **Result**: Confident, complete answers

### 2. Behavioral Interviews
- **Problem**: Struggling to recall STAR examples
- **Solution**: AI provides bullet points from your resume
- **Result**: Structured, impactful responses

### 3. Multilingual Interviews
- **Problem**: Interview in non-native language
- **Solution**: AI responds in same language as question
- **Result**: Natural, fluent communication

### 4. Remote Interviews
- **Problem**: Screen sharing makes notes visible
- **Solution**: Stealth overlay invisible to interviewers
- **Result**: Discreet assistance without detection

---

## 📊 Performance Metrics

| Metric | Value | Details |
|--------|-------|---------|
| **Transcription Latency** | 200-500ms | Groq Whisper API |
| **AI Response Time** | 1-2 seconds | Streaming from Gemini |
| **Transcription Accuracy** | 95%+ | Clear audio conditions |
| **Languages Supported** | 99+ | Auto-detection |
| **Dependencies Size** | ~50MB | Down from 4GB (PyTorch) |
| **Groq Rate Limit** | 30 req/min | Free tier |
| **Gemini Rate Limit** | 60 req/min | Free tier |

---

## 🛠️ Requirements

### System Requirements
- **OS**: Windows 10 (version 2004+) or Windows 11
- **Python**: 3.8 or higher
- **FFmpeg**: Required for audio processing
- **Internet**: Required for API calls

### API Requirements
- **Groq API Key**: Free at [console.groq.com](https://console.groq.com)
- **Gemini API Key**: Free at [aistudio.google.com](https://aistudio.google.com/app/apikey)

### Hardware Requirements
- **Microphone**: Any USB or built-in mic
- **Speakers/Headphones**: For capturing interviewer audio
- **Virtual Audio Cable**: Recommended for online interviews (VB-Cable, Voicemeeter)

---

## 🔧 Installation

### Detailed Installation Steps

1. **Install Python 3.8+**
   ```bash
   python --version  # Verify installation
   ```

2. **Install FFmpeg**
   ```powershell
   # Using Chocolatey (recommended)
   choco install ffmpeg
   
   # Or download from ffmpeg.org
   ```

3. **Clone Repository**
   ```bash
   git clone <repo-url>
   cd ecoute-main
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Get API Keys**
   - Groq: [console.groq.com](https://console.groq.com)
   - Gemini: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

6. **Launch**
   ```bash
   start.bat  # or python launcher.py
   ```

---

## 💡 Usage Tips

### Before the Interview

1. **Test Audio Setup**
   - Launch the app and speak into your mic
   - Verify transcription appears in left panel
   - Play audio and verify speaker capture

2. **Test Stealth Overlay**
   - Start a test Zoom meeting
   - Share your screen
   - Verify overlay is invisible to participants

3. **Prepare Context**
   - Paste your complete resume
   - Add the job description
   - Include specific project details

4. **Position Overlay**
   - Move overlay to convenient location
   - Ensure it doesn't block important content
   - Practice glancing naturally

### During the Interview

1. **Glance, Don't Stare**
   - Brief glances at overlay
   - Natural eye movement
   - Don't read verbatim

2. **Use as Memory Triggers**
   - Bullet points jog your memory
   - Expand in your own words
   - Add personal details

3. **Adapt to Conversation**
   - AI provides starting points
   - Follow the natural flow
   - Don't force all points

4. **Clear When Needed**
   - Click "Clear All" to reset
   - Keeps transcript manageable
   - Resets AI conversation

### After the Interview

1. **Review Transcript**
   - Check what was discussed
   - Note areas for improvement
   - Save for future reference

2. **Close Overlay**
   - Click "✕" to close
   - Or toggle visibility

3. **Prepare for Next**
   - Update context if needed
   - Adjust positioning
   - Test again

---

## 🔒 Privacy & Ethics

### Privacy

- ✅ All data stored locally (`.env`, `temp_context.txt`)
- ✅ API keys never shared or transmitted to third parties
- ✅ Transcriptions sent only to Groq API (see their privacy policy)
- ✅ AI requests sent only to Google Gemini (see their privacy policy)
- ✅ No telemetry or analytics collected

### Ethics

**This tool is designed to:**
- ✅ Help you recall your own experience
- ✅ Reduce interview anxiety
- ✅ Improve communication clarity
- ✅ Present your authentic self

**This tool is NOT designed to:**
- ❌ Fabricate experience you don't have
- ❌ Lie about your skills
- ❌ Impersonate someone else
- ❌ Cheat or deceive

**Recommendations:**
- Use as memory aid, not as script
- Be honest about your experience
- Adapt suggestions to your voice
- Consider disclosing if asked directly

---

## 🐛 Troubleshooting

### Common Issues

**"GROQ_API_KEY not found"**
- Enter key in launcher
- Check `.env` file exists
- Restart application

**"GEMINI_API_KEY not found"**
- Enter key in launcher
- Check `.env` file exists
- Restart application

**No transcription appearing**
- Verify Groq API key is valid
- Check audio devices are selected
- Ensure mic/speakers not muted
- Verify FFmpeg installed: `ffmpeg -version`

**No AI suggestions**
- Check Gemini API key is valid
- Ensure question is >20 characters
- Verify internet connection
- Check console for errors

**Overlay visible in screen sharing**
- Update to Windows 10 (2004+) or Windows 11
- Check console for API error messages
- Test with different screen sharing app
- Some apps may not respect the flag

**Audio devices not showing**
- Check Windows sound settings
- Ensure devices connected and enabled
- Restart launcher
- Run as administrator

---

## 📚 Documentation

- **README.md** (this file) - Complete project overview
- **README_AI_ASSISTANT.md** - AI assistant setup and usage
- **README_GROQ.md** - Groq transcription details
- **LAUNCHER_README.md** - Launcher configuration
- **STEALTH_OVERLAY_GUIDE.md** - Stealth mode guide
- **IMPLEMENTATION_SUMMARY.md** - Technical implementation

---

## 🎓 Credits

- **Original Ecoute**: [SevaSk](https://github.com/SevaSk/ecoute)
- **Groq API**: Ultra-fast Whisper transcription
- **Google Gemini**: AI-powered suggestions
- **CustomTkinter**: Modern UI framework

---

## 📄 License

Same as original Ecoute project.

---

## 🚀 Future Enhancements

- [ ] OpenAI GPT support
- [ ] Claude (Anthropic) support
- [ ] Local LLM support (Ollama)
- [ ] Recording and playback
- [ ] Export transcript to PDF/DOCX
- [ ] Custom prompt templates
- [ ] Keyboard shortcuts
- [ ] macOS support
- [ ] Linux support

---

## 📞 Support

For issues or questions:
1. Check documentation files
2. Review troubleshooting section
3. Open GitHub issue
4. Submit pull request

---

**Built with ❤️ for interview success**

**Project Status**: ✅ Production Ready  
**Last Updated**: 2026-05-18  
**Version**: 1.0.0

---

## ⭐ Star This Project

If this tool helped you succeed in your interviews, please star the repository!

---

**Remember**: This tool helps you present your authentic self. Use it to reduce anxiety and recall your own experience, not to fabricate skills you don't have. Good luck with your interviews! 🎯
