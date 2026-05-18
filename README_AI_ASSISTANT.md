# AI Interview Copilot - Complete Setup Guide

## 🎯 Overview

An AI-powered real-time interview assistant that:
- **Transcribes** both you and the interviewer using Groq's ultra-fast Whisper API
- **Analyzes** interviewer questions in real-time
- **Suggests** 3-4 bullet-point talking points using Google Gemini
- **Adapts** to multiple languages automatically (English, Polish, Ukrainian, Spanish, etc.)
- **Personalizes** responses based on your resume and job description

## 🚀 Quick Start (3 Steps)

### 1. Get Your API Keys (Both Free!)

**Groq API (for transcription):**
1. Visit [console.groq.com](https://console.groq.com)
2. Sign up for free account
3. Create API key
4. Copy the key

**Gemini API (for AI suggestions):**
1. Visit [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required:**
- Python >=3.8.0
- FFmpeg (for audio processing)
- Windows OS

**Install FFmpeg:**
```powershell
choco install ffmpeg
```

### 3. Launch the Application

**One-Click Launch:**
```
Double-click start.bat
```

**Manual Launch:**
```bash
python launcher.py
```

## 📋 Configuration Launcher

When you launch, a configuration window appears:

### Audio Devices
- **Microphone Input**: Your microphone (for capturing your voice)
- **Speaker Output**: Your speakers/headphones (for capturing interviewer's voice)
  - Use a virtual audio cable (like VB-Cable) for online interviews
  - Default devices are automatically selected

### API Configuration
- **Groq API Key**: For speech-to-text transcription
- **Gemini API Key**: For AI-powered interview suggestions

### Interview Context
- **Paste your resume** and/or **job description**
- This helps the AI provide personalized, relevant suggestions
- Saved to `temp_context.txt` for future sessions

### Start Button
Click the green **START** button to launch the main application.

## 🎨 Main Application Interface

### Split-Screen Layout (1400x700)

**Left Panel - Live Transcript (60%)**
- Real-time transcription of the conversation
- **You**: Your responses (from microphone)
- **Speaker**: Interviewer's questions (from speakers)
- Most recent messages appear at the top

**Right Panel - AI Suggestions (40%)**
- Real-time AI-generated talking points
- Appears automatically when interviewer asks a question
- Streams token-by-token for minimal latency
- Green text for easy visibility

### Controls
- **Clear All**: Resets transcript and AI conversation history

## 🤖 How the AI Assistant Works

### System Prompt Architecture

The AI is engineered with a strict prompt that:

1. **Analyzes** the interviewer's question in real-time
2. **Responds** with exactly 3-4 short bullet points
3. **Uses** keywords and phrases (NOT full sentences)
4. **References** your specific projects/experience from the context
5. **Matches** the interviewer's language automatically

### Response Format

**What you get:**
```
• Optimized database queries - reduced latency 60%
• Implemented caching layer with Redis
• Collaborated with DevOps on infrastructure
• Result: handled 10x traffic spike
```

**What you DON'T get:**
```
Here are some points you could mention:
- You should talk about the time when you optimized...
- It would be good to mention that you worked with...
```

### Multilingual Support

The AI automatically detects and responds in the same language as the interviewer:

**English Question:**
```
Interviewer: "Tell me about your experience with React"
AI: 
• 3 years commercial experience
• Built SPA with React Hooks and Context API
• Integrated REST API and GraphQL
• Performance optimization - lazy loading
```

**Polish Question:**
```
Interviewer: "Jakie masz doświadczenie z React?"
AI:
• 3 lata komercyjnego doświadczenia
• Budowa SPA z React Hooks i Context API
• Integracja z REST API i GraphQL
• Optymalizacja wydajności - lazy loading
```

**Ukrainian Question:**
```
Interviewer: "Розкажіть про ваш досвід з React"
AI:
• 3 роки комерційного досвіду
• Розробка SPA з React Hooks та Context API
• Інтеграція з REST API та GraphQL
• Оптимізація продуктивності - lazy loading
```

## 🔧 Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    launcher.py (Entry Point)                 │
│  - Audio device selection                                    │
│  - API key configuration (Groq + Gemini)                     │
│  - Interview context input                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    Saves to .env file
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│  - Initializes audio recorders                               │
│  - Starts transcription threads                              │
│  - Creates dual-pane UI                                      │
│  - Manages LLM client                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                                             ↓
┌──────────────────────┐                  ┌──────────────────────┐
│  AudioRecorder.py    │                  │  LLMClient.py        │
│  - Captures mic      │                  │  - Loads context     │
│  - Captures speakers │                  │  - Builds prompt     │
│  - Sends to queues   │                  │  - Streams responses │
└──────────────────────┘                  └──────────────────────┘
        ↓                                             ↑
┌──────────────────────┐                              │
│ TranscriberModels.py │                              │
│  - Groq Whisper API  │                              │
│  - whisper-large-v3  │                              │
└──────────────────────┘                              │
        ↓                                             │
┌──────────────────────┐                              │
│ AudioTranscriber.py  │                              │
│  - Processes audio   │                              │
│  - Generates text    │──────────────────────────────┘
│  - Triggers AI       │   (Latest speaker text)
└──────────────────────┘
```

## 📁 Project Structure

```
├── launcher.py              # Configuration GUI (entry point)
├── start.bat               # One-click launcher
├── main.py                 # Main application with dual-pane UI
├── LLMClient.py            # AI client manager (Gemini integration)
├── AudioRecorder.py        # Audio capture from mic/speakers
├── AudioTranscriber.py     # Transcription orchestration
├── TranscriberModels.py    # Groq API integration
├── requirements.txt        # Python dependencies
├── .env                    # API keys & config (auto-generated)
├── .env.example            # Template for .env
├── temp_context.txt        # Interview context (auto-generated)
├── README_GROQ.md          # Groq transcription documentation
└── LAUNCHER_README.md      # Launcher documentation
```

## 🔑 Environment Variables

The `.env` file (auto-generated by launcher) contains:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxx
MIC_DEVICE_INDEX=1
SPEAKER_DEVICE_INDEX=5
```

## 📊 Performance Metrics

### Transcription (Groq Whisper)
- **Latency**: 200-500ms
- **Accuracy**: 95%+ for clear audio
- **Languages**: 99+ languages supported
- **Rate Limits**: 30 requests/min (free tier)

### AI Suggestions (Gemini)
- **Latency**: 1-2 seconds (streaming)
- **Token Limit**: 300 tokens per response
- **Context Window**: Full conversation history
- **Rate Limits**: 60 requests/min (free tier)

## 🛠️ Troubleshooting

### "GROQ_API_KEY not found"
- Ensure you entered the key in the launcher
- Check `.env` file exists and contains the key
- Restart the application

### "GEMINI_API_KEY not found"
- Ensure you entered the key in the launcher
- Check `.env` file exists and contains the key
- Restart the application

### No AI suggestions appearing
- Check that interviewer's question is >20 characters
- Verify Gemini API key is valid
- Check console for error messages
- Ensure internet connection is active

### Transcription not working
- Verify Groq API key is valid
- Check audio devices are selected correctly
- Ensure microphone/speakers are not muted
- Check FFmpeg is installed: `ffmpeg -version`

### Audio devices not showing
- Check Windows sound settings
- Ensure devices are connected and enabled
- Restart the launcher
- Try running as administrator

### AI responds in wrong language
- The AI automatically detects language from the question
- Ensure the transcription is accurate (check left panel)
- If transcription is wrong, check audio quality

### "Failed to initialize LLM client"
- Check Gemini API key is correct
- Verify `google-generativeai` package is installed
- Check internet connection
- Application will continue without AI suggestions

## 💡 Tips for Best Results

### Audio Setup
1. **Use a virtual audio cable** (VB-Cable, Voicemeeter) for online interviews
2. **Test audio levels** before the interview
3. **Minimize background noise** for better transcription
4. **Use headphones** to prevent echo/feedback

### Context Optimization
1. **Include specific projects** with technologies and results
2. **Add quantifiable achievements** (percentages, numbers, impact)
3. **List relevant skills** for the target role
4. **Keep it concise** (500-1000 words is ideal)

### During the Interview
1. **Glance at suggestions** - don't read them verbatim
2. **Use as memory triggers** - expand in your own words
3. **Adapt to the conversation** - AI provides starting points
4. **Clear transcript periodically** to keep it manageable

## 🔒 Privacy & Security

- **API keys** are stored locally in `.env` file (never shared)
- **Interview context** is stored locally in `temp_context.txt`
- **Transcriptions** are sent to Groq API (see their privacy policy)
- **AI requests** are sent to Google Gemini (see their privacy policy)
- **No data** is stored on our servers (we don't have any!)

## 📈 Future Enhancements

- [ ] Support for OpenAI GPT models
- [ ] Support for Claude (Anthropic)
- [ ] Local LLM support (Ollama)
- [ ] Recording and playback of interviews
- [ ] Export transcript to PDF/DOCX
- [ ] Custom prompt templates
- [ ] Multi-language UI
- [ ] macOS and Linux support

## 🤝 Contributing

This is a refactored version of [Ecoute](https://github.com/SevaSk/ecoute) by SevaSk.

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📄 License

Same as original Ecoute project.

## 🙏 Credits

- **Original Ecoute**: [SevaSk](https://github.com/SevaSk)
- **Groq API**: Ultra-fast Whisper transcription
- **Google Gemini**: AI-powered suggestions
- **CustomTkinter**: Modern UI framework

---

**Built with ❤️ for interview success**

Last updated: 2026-05-18
