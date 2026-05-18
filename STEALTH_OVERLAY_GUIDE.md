# Stealth Overlay - Screen Capture Exclusion Feature

## Overview

The Stealth Overlay is a frameless, always-on-top window that displays AI suggestions during interviews while remaining **invisible to screen sharing applications** like Zoom, Teams, Google Meet, and OBS.

## Key Features

### 1. Screen Capture Exclusion
Uses Windows API `SetWindowDisplayAffinity` with `WDA_EXCLUDEFROMCAPTURE` flag to exclude the window from screen capture. This means:
- ✅ You can see the overlay on your screen
- ✅ Interviewers see a black box or nothing at all
- ✅ Works with Zoom, Teams, Meet, OBS, and other screen capture tools

### 2. Visual Design
- **Frameless**: No title bar or window borders
- **Always on Top**: Stays above all other windows
- **Semi-transparent**: 85% opacity with dark background
- **Draggable**: Click and hold anywhere to move
- **Discrete Close Button**: Small "✕" in the corner

### 3. Real-time Streaming
- Receives AI suggestions token-by-token
- Auto-scrolls to show latest content
- Thread-safe text updates
- Synchronized with main UI

## Usage

### Automatic Launch
The stealth overlay automatically appears when you start the main application.

### Manual Control
- **Toggle Visibility**: Click "Toggle Stealth Overlay" button in main UI
- **Move Window**: Click and drag anywhere on the overlay
- **Close**: Click the "✕" button in the top-right corner

### Positioning
1. Launch the application
2. Position the overlay in a convenient location (e.g., corner of screen)
3. The overlay will stay on top of all windows including:
   - Zoom meeting window
   - Browser (Google Meet)
   - Microsoft Teams
   - Any other application

## Testing Screen Capture Exclusion

### Test with Zoom
1. Start a Zoom meeting
2. Launch the AI Interview Copilot
3. Position the stealth overlay on your screen
4. Click "Share Screen" in Zoom
5. Select your entire screen or a specific window
6. **Result**: The overlay should appear as a black box or be invisible to participants

### Test with OBS Studio
1. Open OBS Studio
2. Add a "Display Capture" or "Window Capture" source
3. Launch the AI Interview Copilot
4. Position the stealth overlay in the capture area
5. **Result**: The overlay should appear as a black box in the OBS preview

### Test with Microsoft Teams
1. Start a Teams meeting
2. Launch the AI Interview Copilot
3. Click "Share" → "Desktop"
4. **Result**: The overlay should be invisible to other participants

### Test with Google Meet
1. Start a Google Meet
2. Launch the AI Interview Copilot
3. Click "Present now" → "Your entire screen"
4. **Result**: The overlay should be invisible to other participants

## Technical Implementation

### Windows API Call
```python
import ctypes

# Get window handle
hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())

# Apply screen capture exclusion
WDA_EXCLUDEFROMCAPTURE = 0x00000011
result = ctypes.windll.user32.SetWindowDisplayAffinity(
    hwnd,
    WDA_EXCLUDEFROMCAPTURE
)
```

### How It Works
1. The overlay window is created using CustomTkinter
2. After window creation, we get the Windows handle (HWND)
3. We call `SetWindowDisplayAffinity` with `WDA_EXCLUDEFROMCAPTURE`
4. Windows marks the window as excluded from screen capture
5. Screen sharing applications respect this flag and exclude the window

## Limitations

### Windows Only
- The `SetWindowDisplayAffinity` API is Windows-specific
- macOS and Linux require different approaches
- Future versions may add cross-platform support

### Windows 10/11 Required
- This feature requires Windows 10 (version 2004) or later
- Older Windows versions may not support this API

### Some Applications May Not Respect the Flag
- Most modern screen sharing apps respect the flag
- Some older or custom screen capture tools may ignore it
- Always test with your specific interview platform

## Troubleshooting

### Overlay is visible in screen sharing
**Possible causes:**
1. Windows version is too old (< Windows 10 2004)
2. Screen sharing app doesn't respect the flag
3. API call failed (check console for errors)

**Solutions:**
- Update to Windows 10 (version 2004) or later
- Check console output for error messages
- Try a different screen sharing application
- Use a virtual machine or second monitor as fallback

### Overlay doesn't appear
**Possible causes:**
1. Window was created but is hidden
2. Window is positioned off-screen
3. Application crashed during initialization

**Solutions:**
- Click "Toggle Stealth Overlay" button
- Check console for error messages
- Restart the application
- Check that all dependencies are installed

### Can't move the overlay
**Possible causes:**
1. Clicking on a non-draggable element
2. Window is locked by another application

**Solutions:**
- Click and drag on the dark background area
- Avoid clicking on the text area
- Close and reopen the overlay

### Text is not updating
**Possible causes:**
1. LLM client failed to initialize
2. No interviewer questions detected
3. Thread synchronization issue

**Solutions:**
- Check that Gemini API key is valid
- Ensure interviewer's question is >20 characters
- Check console for error messages
- Restart the application

## Best Practices

### Before the Interview
1. **Test the overlay** with your interview platform
2. **Position the overlay** in a convenient location
3. **Verify screen capture exclusion** by recording your screen
4. **Practice glancing** at the overlay naturally

### During the Interview
1. **Glance briefly** - don't stare at the overlay
2. **Use as memory triggers** - don't read verbatim
3. **Adapt to conversation** - AI provides starting points
4. **Keep it subtle** - natural eye movement is key

### After the Interview
1. **Close the overlay** or hide it
2. **Review the transcript** in the main UI
3. **Clear the conversation** for next interview

## Privacy & Ethics

### Ethical Considerations
- This tool is designed to help you recall your own experience
- It's meant to reduce anxiety and improve communication
- Always be honest about your skills and experience
- Use the suggestions as memory aids, not as scripts

### Legal Considerations
- Check your local laws regarding interview assistance tools
- Some jurisdictions may have specific rules
- When in doubt, disclose the use of assistance tools
- Respect the interviewer's and company's policies

### Transparency
- The tool helps you present your authentic self
- It doesn't fabricate experience or skills
- It's based on your own resume and context
- Consider it similar to having notes during a phone interview

## Advanced Configuration

### Changing Opacity
Edit `StealthOverlay.py` line 35:
```python
self.root.attributes('-alpha', 0.85)  # Change 0.85 to desired value (0.0-1.0)
```

### Changing Window Size
Edit `StealthOverlay.py` line 32:
```python
self.root.geometry("400x300+100+100")  # width x height + x + y
```

### Changing Text Color
Edit `StealthOverlay.py` line 95:
```python
text_color="#2ecc71"  # Change to desired color (hex code)
```

### Changing Font Size
Edit `StealthOverlay.py` line 94:
```python
font=("Arial", 16, "bold")  # Change 16 to desired size
```

## Testing the Overlay

### Standalone Test
```bash
python StealthOverlay.py
```

This will:
1. Create a test overlay window
2. Simulate streaming text
3. Allow you to test dragging and positioning
4. Verify screen capture exclusion

### Integration Test
1. Launch the full application: `python launcher.py`
2. Configure settings and click START
3. Verify overlay appears automatically
4. Test with screen sharing application
5. Verify AI suggestions stream to overlay

## Keyboard Shortcuts (Future Enhancement)

Planned keyboard shortcuts:
- `Ctrl+H`: Hide/Show overlay
- `Ctrl+M`: Move overlay to predefined position
- `Ctrl+R`: Reset overlay size and position
- `Ctrl+Q`: Close overlay

## Support

If you encounter issues with the stealth overlay:
1. Check console output for error messages
2. Verify Windows version (10 2004+ required)
3. Test with different screen sharing applications
4. Review the troubleshooting section above
5. Open a GitHub issue with details

---

**Remember**: This tool is designed to help you succeed in interviews by reducing anxiety and helping you recall your own experience. Use it responsibly and ethically.

Last updated: 2026-05-18
