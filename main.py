import threading
from AudioTranscriber import AudioTranscriber
import customtkinter as ctk
import AudioRecorder
import time
import subprocess
import os
from dotenv import load_dotenv
from LLMClient import LLMClient
from StealthOverlay import StealthOverlayManager

def write_in_textbox(textbox, text):
    textbox.delete("0.0", "end")
    textbox.insert("0.0", text)

def update_transcript_UI(transcriber, transcript_textbox, suggestion_textbox, llm_client, overlay_manager):
    transcript_string = transcriber.get_transcript()
    write_in_textbox(transcript_textbox, transcript_string)

    latest_speaker_text = transcriber.get_latest_speaker_text()
    if latest_speaker_text and len(latest_speaker_text.strip()) > 20:
        if not hasattr(update_transcript_UI, 'last_processed') or update_transcript_UI.last_processed != latest_speaker_text:
            update_transcript_UI.last_processed = latest_speaker_text

            threading.Thread(
                target=get_ai_suggestion,
                args=(latest_speaker_text, suggestion_textbox, llm_client, overlay_manager),
                daemon=True
            ).start()

    transcript_textbox.after(300, update_transcript_UI, transcriber, transcript_textbox, suggestion_textbox, llm_client, overlay_manager)

def get_ai_suggestion(interviewer_question, suggestion_textbox, llm_client, overlay_manager):
    try:
        suggestion_textbox.delete("0.0", "end")
        suggestion_textbox.insert("0.0", "🤔 Thinking...\n")

        full_response = ""
        response_generator = llm_client.get_suggestion(interviewer_question)

        # Stream to both the main UI and the stealth overlay
        overlay_manager.stream_suggestions(llm_client.get_suggestion(interviewer_question))

        for token in response_generator:
            full_response += token
            suggestion_textbox.delete("0.0", "end")
            suggestion_textbox.insert("0.0", full_response)
            suggestion_textbox.update()

    except Exception as e:
        print(f"[ERROR] Failed to get AI suggestion: {e}")
        suggestion_textbox.delete("0.0", "end")
        suggestion_textbox.insert("0.0", "❌ AI suggestion failed")
        overlay_manager.update_suggestions("❌ AI suggestion failed", clear=True)

def clear_context(transcriber, suggestion_textbox, llm_client, overlay_manager):
    transcriber.clear_transcript_data()

    suggestion_textbox.delete("0.0", "end")
    llm_client.reset_conversation()
    overlay_manager.update_suggestions("Waiting for interviewer's question...\n\n", clear=True)

    if hasattr(update_transcript_UI, 'last_processed'):
        delattr(update_transcript_UI, 'last_processed')

def create_ui_components(root, transcriber, llm_client, overlay_manager):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root.title("AI Interview Copilot")
    root.geometry("1400x700")

    root.grid_columnconfigure(0, weight=2)
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=1)

    left_frame = ctk.CTkFrame(root)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
    left_frame.grid_columnconfigure(0, weight=1)
    left_frame.grid_rowconfigure(0, weight=0)
    left_frame.grid_rowconfigure(1, weight=1)
    left_frame.grid_rowconfigure(2, weight=0)

    transcript_label = ctk.CTkLabel(
        left_frame,
        text="📝 Live Transcript",
        font=("Arial", 18, "bold")
    )
    transcript_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

    transcript_textbox = ctk.CTkTextbox(
        left_frame,
        font=("Arial", 16),
        text_color='#FFFCF2',
        wrap="word"
    )
    transcript_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    clear_button = ctk.CTkButton(
        left_frame,
        text="Clear All",
        command=lambda: clear_context(transcriber, suggestion_textbox, llm_client, overlay_manager),
        height=40
    )
    clear_button.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

    right_frame = ctk.CTkFrame(root)
    right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
    right_frame.grid_columnconfigure(0, weight=1)
    right_frame.grid_rowconfigure(0, weight=0)
    right_frame.grid_rowconfigure(1, weight=1)
    right_frame.grid_rowconfigure(2, weight=0)

    suggestion_label = ctk.CTkLabel(
        right_frame,
        text="💡 AI Suggestions",
        font=("Arial", 18, "bold")
    )
    suggestion_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

    suggestion_textbox = ctk.CTkTextbox(
        right_frame,
        font=("Arial", 18),
        text_color='#2ecc71',
        wrap="word"
    )
    suggestion_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    suggestion_textbox.insert("0.0", "Waiting for interviewer's question...")

    toggle_overlay_button = ctk.CTkButton(
        right_frame,
        text="Toggle Stealth Overlay",
        command=overlay_manager.toggle_visibility,
        height=40,
        fg_color="#9b59b6",
        hover_color="#8e44ad"
    )
    toggle_overlay_button.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

    return transcript_textbox, suggestion_textbox

def main():
    load_dotenv()

    mic_device_index = os.getenv("MIC_DEVICE_INDEX")
    speaker_device_index = os.getenv("SPEAKER_DEVICE_INDEX")

    if mic_device_index:
        mic_device_index = int(mic_device_index)
    else:
        mic_device_index = None

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
        llm_client = LLMClient(provider="gemini")
        print("[INFO] LLM client initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize LLM client: {e}")
        print("[WARNING] Continuing without AI suggestions")
        llm_client = None

    root = ctk.CTk()

    # Cleanup function to remove temp files on exit
    def cleanup_on_exit():
        print("[INFO] Cleaning up temporary files...")
        try:
            if os.path.exists("temp_context.txt"):
                os.remove("temp_context.txt")
                print("[INFO] Removed temp_context.txt")
        except Exception as e:
            print(f"[WARNING] Failed to cleanup temp files: {e}")

    # Register cleanup function
    root.protocol("WM_DELETE_WINDOW", lambda: (cleanup_on_exit(), root.destroy()))

    # Create stealth overlay manager
    overlay_manager = StealthOverlayManager()
    overlay_manager.create_overlay()
    print("[INFO] Stealth overlay created")

    # Create audio recorders with error handling
    try:
        mic_recorder = AudioRecorder.DefaultMicRecorder(device_index=mic_device_index)
        speaker_recorder = AudioRecorder.DefaultSpeakerRecorder(device_index=speaker_device_index)

        # Create transcriber with new pure Groq API pipeline
        transcriber = AudioTranscriber(mic_recorder, speaker_recorder)
        transcriber.start()

        transcript_textbox, suggestion_textbox = create_ui_components(root, transcriber, llm_client, overlay_manager)

        print("READY")

        if llm_client:
            update_transcript_UI(transcriber, transcript_textbox, suggestion_textbox, llm_client, overlay_manager)
        else:
            def update_transcript_no_llm():
                transcript_string = transcriber.get_transcript()
                write_in_textbox(transcript_textbox, transcript_string)
                transcript_textbox.after(300, update_transcript_no_llm)
            update_transcript_no_llm()

        root.mainloop()

        # Final cleanup after mainloop exits
        transcriber.close()
        cleanup_on_exit()

    except Exception as e:
        print(f"[ERROR] Failed to initialize audio system: {e}")

        # Create minimal UI to show error
        transcript_textbox, suggestion_textbox = create_ui_components(root, None, llm_client, overlay_manager)

        error_message = f"❌ Audio Initialization Failed\n\n{str(e)}\n\nPossible causes:\n• Invalid audio device selected\n• Audio device disconnected\n• Sample rate not supported\n\nPlease restart and select different audio devices."
        write_in_textbox(transcript_textbox, error_message)
        write_in_textbox(suggestion_textbox, "Audio system unavailable")

        root.mainloop()
        cleanup_on_exit()

if __name__ == "__main__":
    main()