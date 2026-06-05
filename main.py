import threading
from AudioTranscriber import AudioTranscriber
import customtkinter as ctk
import AudioRecorder
import time
import subprocess
import os
import ctypes
from dotenv import load_dotenv
from LLMClient import LLMClient
from StealthOverlay import StealthOverlayManager

# Windows API constants for stealth mode
WDA_EXCLUDEFROMCAPTURE = 0x00000011
GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080

# Global flag for tracking generation status
is_generating = False

def apply_total_stealth(window):
    """
    Apply complete stealth mode to the main window:
    1. Hide from screen capture (Zoom, Teams, OBS)
    2. Hide from Windows Taskbar
    3. Hide from Alt+Tab menu
    """
    try:
        window.update()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())

        if hwnd:
            # 1. Exclude from screen capture
            result = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            if result:
                print("[INFO] Main window excluded from screen capture")
            else:
                print("[WARNING] Failed to exclude main window from screen capture")

            # 2. Hide from Taskbar and Alt+Tab
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            new_style = (ex_style & ~WS_EX_APPWINDOW) | WS_EX_TOOLWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

            # Force window to update its style
            window.withdraw()
            window.deiconify()

            print("[INFO] Main window hidden from Taskbar and Alt+Tab")
        else:
            print("[WARNING] Could not get window handle for stealth mode")

    except Exception as e:
        print(f"[ERROR] Failed to apply total stealth: {e}")

def write_in_textbox(textbox, text):
    textbox.delete("0.0", "end")
    textbox.insert("0.0", text)

def update_transcript_UI(transcriber, transcript_textbox, suggestion_textbox, llm_client, overlay_manager, status_indicator):
    global is_generating

    # Update status indicators in real-time
    speaker_status = transcriber.get_statuses()
    status_indicator.configure(text=f"{speaker_status} Speaker")

    # Update transcript
    transcript_string = transcriber.get_transcript()
    write_in_textbox(transcript_textbox, transcript_string)

    latest_speaker_text = transcriber.get_latest_speaker_text()
    if latest_speaker_text and len(latest_speaker_text.strip()) > 20:
        if not hasattr(update_transcript_UI, 'last_processed') or update_transcript_UI.last_processed != latest_speaker_text:

            if not is_generating:
                update_transcript_UI.last_processed = latest_speaker_text
                is_generating = True

                def thread_target():
                    global is_generating
                    try:
                        get_ai_suggestion(latest_speaker_text, suggestion_textbox, llm_client, overlay_manager)
                    finally:
                        is_generating = False

                threading.Thread(target=thread_target, daemon=True).start()

    transcript_textbox.after(300, update_transcript_UI, transcriber, transcript_textbox, suggestion_textbox, llm_client, overlay_manager, status_indicator)

def get_ai_suggestion(interviewer_question, suggestion_textbox, llm_client, overlay_manager):
    try:
        suggestion_textbox.delete("0.0", "end")
        suggestion_textbox.insert("0.0", "🤔 Analyzing question...\n")

        full_response = ""
        response_generator = llm_client.get_suggestion(interviewer_question)

        # Clear overlay before new response
        overlay_manager.update_suggestions("", clear=True)

        # Stream tokens to both dashboard and overlay
        for token in response_generator:
            full_response += token

            # Update dashboard
            suggestion_textbox.delete("0.0", "end")
            suggestion_textbox.insert("0.0", full_response)
            suggestion_textbox.update()

            # Stream to overlay
            overlay_manager.update_suggestions(token, clear=False)

    except Exception as e:
        print(f"[ERROR] Failed to get AI suggestion: {e}")
        suggestion_textbox.delete("0.0", "end")
        suggestion_textbox.insert("0.0", "❌ AI suggestion failed")
        overlay_manager.update_suggestions("❌ AI suggestion failed", clear=True)

def clear_context(transcriber, suggestion_textbox, llm_client, overlay_manager):
    transcriber.clear_transcript_data()

    suggestion_textbox.delete("0.0", "end")
    suggestion_textbox.insert("0.0", "Ready for next question...")
    llm_client.reset_conversation()
    overlay_manager.update_suggestions("Ready for next question...", clear=True)

    if hasattr(update_transcript_UI, 'last_processed'):
        delattr(update_transcript_UI, 'last_processed')

def create_ui_components(root, transcriber, llm_client, overlay_manager):
    root.title("AI Ecoute")
    root.geometry("1600x900")

    # Premium color palette
    bg_dark = "#0F172A"
    sidebar_bg = "#1E293B"
    card_bg = "#1E293B"
    accent_blue = "#38BDF8"
    accent_purple = "#A78BFA"
    text_primary = "#F8FAFC"
    text_secondary = "#CBD5E1"
    text_muted = "#94A3B8"
    border_color = "#334155"

    root.configure(fg_color=bg_dark)

    # Grid layout: left panel (transcript) + right panel (AI suggestions)
    root.grid_columnconfigure(0, weight=3)
    root.grid_columnconfigure(1, weight=2)
    root.grid_rowconfigure(0, weight=1)

    # Premium typography
    title_font = ("Segoe UI", 22, "bold")
    content_font = ("Segoe UI", 16)
    status_font = ("Segoe UI", 13)
    button_font = ("Segoe UI", 15, "bold")

    # ========== LEFT PANEL: Live Transcript ==========
    left_panel = ctk.CTkFrame(root, fg_color=card_bg, corner_radius=0)
    left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 1), pady=0)
    left_panel.grid_columnconfigure(0, weight=1)
    left_panel.grid_rowconfigure(2, weight=1)

    # Header with title and status indicators
    header_container = ctk.CTkFrame(left_panel, fg_color="transparent")
    header_container.grid(row=0, column=0, sticky="ew", padx=35, pady=(30, 5))
    header_container.grid_columnconfigure(1, weight=1)

    transcript_title = ctk.CTkLabel(
        header_container,
        text="📝 Live Transcript",
        font=title_font,
        text_color=text_primary,
        anchor="w"
    )
    transcript_title.grid(row=0, column=0, sticky="w")

    # Status indicator with visual dots
    status_indicator = ctk.CTkLabel(
        header_container,
        text="⚪ Speaker",
        font=status_font,
        text_color=text_muted,
        anchor="e"
    )
    status_indicator.grid(row=0, column=1, sticky="e", padx=(10, 0))

    # Subtitle
    subtitle_label = ctk.CTkLabel(
        left_panel,
        text="Real-time conversation transcription",
        font=("Segoe UI", 13),
        text_color=text_muted,
        anchor="w"
    )
    subtitle_label.grid(row=1, column=0, sticky="w", padx=35, pady=(5, 20))

    # Transcript textbox - clean, spacious design
    transcript_textbox = ctk.CTkTextbox(
        left_panel,
        font=content_font,
        text_color=text_secondary,
        fg_color=bg_dark,
        border_width=0,
        corner_radius=0,
        wrap="word",
        spacing1=8,
        spacing3=8
    )
    transcript_textbox.grid(row=2, column=0, sticky="nsew", padx=35, pady=(0, 20))

    # Clear button with subtle styling
    clear_button = ctk.CTkButton(
        left_panel,
        text="Clear Session",
        font=button_font,
        height=50,
        corner_radius=10,
        fg_color=border_color,
        hover_color="#475569",
        text_color=text_primary,
        command=lambda: clear_context(transcriber, None, llm_client, overlay_manager)
    )
    clear_button.grid(row=3, column=0, sticky="ew", padx=35, pady=(0, 30))

    # ========== RIGHT PANEL: AI Copilot ==========
    right_panel = ctk.CTkFrame(root, fg_color=card_bg, corner_radius=0)
    right_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
    right_panel.grid_columnconfigure(0, weight=1)
    right_panel.grid_rowconfigure(2, weight=1)

    # AI Copilot header with gradient-style accent
    ai_header_container = ctk.CTkFrame(right_panel, fg_color="transparent")
    ai_header_container.grid(row=0, column=0, sticky="ew", padx=35, pady=(30, 5))

    ai_title = ctk.CTkLabel(
        ai_header_container,
        text="💡Ecoute",
        font=title_font,
        text_color=accent_blue,
        anchor="w"
    )
    ai_title.grid(row=0, column=0, sticky="w")

    # AI subtitle
    ai_subtitle = ctk.CTkLabel(
        right_panel,
        text="Instant talking points powered by local LLM",
        font=("Segoe UI", 13),
        text_color=text_muted,
        anchor="w"
    )
    ai_subtitle.grid(row=1, column=0, sticky="w", padx=35, pady=(5, 20))

    # AI suggestion textbox - prominent, high-contrast
    suggestion_textbox = ctk.CTkTextbox(
        right_panel,
        font=("Segoe UI", 17),
        text_color=accent_blue,
        fg_color=bg_dark,
        border_width=0,
        corner_radius=0,
        wrap="word",
        spacing1=10,
        spacing3=10
    )
    suggestion_textbox.grid(row=2, column=0, sticky="nsew", padx=35, pady=(0, 20))
    suggestion_textbox.insert("0.0", "Waiting for interviewer's question...")

    # Toggle overlay button - vibrant accent
    toggle_overlay_button = ctk.CTkButton(
        right_panel,
        text="Toggle Stealth Overlay",
        font=button_font,
        height=50,
        corner_radius=10,
        fg_color="#2563EB",
        hover_color="#1D4ED8",
        text_color=text_primary,
        command=overlay_manager.toggle_visibility
    )
    toggle_overlay_button.grid(row=3, column=0, sticky="ew", padx=35, pady=(0, 30))

    # Fix clear button lambda
    clear_button.configure(command=lambda: clear_context(transcriber, suggestion_textbox, llm_client, overlay_manager))

    return transcript_textbox, suggestion_textbox, status_indicator

def main():
    load_dotenv()

    speaker_device_index = os.getenv("SPEAKER_DEVICE_INDEX")

    if speaker_device_index:
        speaker_device_index = int(speaker_device_index)
    else:
        speaker_device_index = None

    context_file = "temp_context.txt"
    if os.path.exists(context_file):
        with open(context_file, "r", encoding="utf-8") as f:
            interview_context = f.read()
            print(f"[INFO] Loaded interview context ({len(interview_context)} characters)")
    else:
        interview_context = ""
        print("[INFO] No interview context found")

    try:
        llm_client = LLMClient(provider="local")
        print("[INFO] LLM client initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize LLM client: {e}")
        print("[WARNING] Continuing without AI suggestions")
        llm_client = None

    root = ctk.CTk()

    # Apply total stealth mode to main window
    apply_total_stealth(root)

    def cleanup_on_exit():
        print("[INFO] Cleaning up temporary files...")
        try:
            if os.path.exists("temp_context.txt"):
                os.remove("temp_context.txt")
                print("[INFO] Removed temp_context.txt")
        except Exception as e:
            print(f"[WARNING] Failed to cleanup temp files: {e}")

    def hard_exit():
        print("[INFO] Initiating hard exit...")
        cleanup_on_exit()
        try:
            transcriber.close()
        except:
            pass
        os._exit(0)

    overlay_manager = StealthOverlayManager()
    overlay_manager.create_overlay()
    print("[INFO] Stealth overlay created")

    try:
        speaker_recorder = AudioRecorder.DefaultSpeakerRecorder(device_index=speaker_device_index)

        transcriber = AudioTranscriber(speaker_recorder)
        transcriber.start()

        root.protocol("WM_DELETE_WINDOW", hard_exit)

        transcript_textbox, suggestion_textbox, status_indicator = create_ui_components(root, transcriber, llm_client, overlay_manager)

        print("READY")

        if llm_client:
            update_transcript_UI(transcriber, transcript_textbox, suggestion_textbox, llm_client, overlay_manager, status_indicator)
        else:
            def update_transcript_no_llm():
                transcript_string = transcriber.get_transcript()
                write_in_textbox(transcript_textbox, transcript_string)
                transcript_textbox.after(300, update_transcript_no_llm)
            update_transcript_no_llm()

        root.mainloop()

    except Exception as e:
        print(f"[ERROR] Failed to initialize audio system: {e}")

        root.protocol("WM_DELETE_WINDOW", lambda: (cleanup_on_exit(), os._exit(0)))

        transcript_textbox, suggestion_textbox, status_indicator = create_ui_components(root, None, llm_client, overlay_manager)

        error_message = f"❌ Audio Initialization Failed\n\n{str(e)}\n\nPossible causes:\n• Invalid audio device selected\n• Audio device disconnected\n• Sample rate not supported\n\nPlease restart and select different audio devices."
        write_in_textbox(transcript_textbox, error_message)
        write_in_textbox(suggestion_textbox, "Audio system unavailable")

        root.mainloop()

if __name__ == "__main__":
    main()
