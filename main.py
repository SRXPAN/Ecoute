import threading
from AudioTranscriber import AudioTranscriber
import customtkinter as ctk
import AudioRecorder
import queue
import time
import sys
import TranscriberModels
import subprocess
import os
from dotenv import load_dotenv
from LLMClient import LLMClient

def write_in_textbox(textbox, text):
    textbox.delete("0.0", "end")
    textbox.insert("0.0", text)

def update_transcript_UI(transcriber, transcript_textbox, suggestion_textbox, llm_client):
    transcript_string = transcriber.get_transcript()
    write_in_textbox(transcript_textbox, transcript_string)

    latest_speaker_text = transcriber.get_latest_speaker_text()
    if latest_speaker_text and len(latest_speaker_text.strip()) > 20:
        if not hasattr(update_transcript_UI, 'last_processed') or update_transcript_UI.last_processed != latest_speaker_text:
            update_transcript_UI.last_processed = latest_speaker_text

            threading.Thread(
                target=get_ai_suggestion,
                args=(latest_speaker_text, suggestion_textbox, llm_client),
                daemon=True
            ).start()

    transcript_textbox.after(300, update_transcript_UI, transcriber, transcript_textbox, suggestion_textbox, llm_client)

def get_ai_suggestion(interviewer_question, suggestion_textbox, llm_client):
    try:
        suggestion_textbox.delete("0.0", "end")
        suggestion_textbox.insert("0.0", "🤔 Thinking...\n")

        full_response = ""
        for token in llm_client.get_suggestion(interviewer_question):
            full_response += token
            suggestion_textbox.delete("0.0", "end")
            suggestion_textbox.insert("0.0", full_response)
            suggestion_textbox.update()

    except Exception as e:
        print(f"[ERROR] Failed to get AI suggestion: {e}")
        suggestion_textbox.delete("0.0", "end")
        suggestion_textbox.insert("0.0", "❌ AI suggestion failed")

def clear_context(transcriber, speaker_queue, mic_queue, suggestion_textbox, llm_client):
    transcriber.clear_transcript_data()

    with speaker_queue.mutex:
        speaker_queue.queue.clear()
    with mic_queue.mutex:
        mic_queue.queue.clear()

    suggestion_textbox.delete("0.0", "end")
    llm_client.reset_conversation()

    if hasattr(update_transcript_UI, 'last_processed'):
        delattr(update_transcript_UI, 'last_processed')

def create_ui_components(root, transcriber, speaker_queue, mic_queue, llm_client):
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
        command=lambda: clear_context(transcriber, speaker_queue, mic_queue, suggestion_textbox, llm_client),
        height=40
    )
    clear_button.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

    right_frame = ctk.CTkFrame(root)
    right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
    right_frame.grid_columnconfigure(0, weight=1)
    right_frame.grid_rowconfigure(0, weight=0)
    right_frame.grid_rowconfigure(1, weight=1)

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

    return transcript_textbox, suggestion_textbox

def main():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("ERROR: The ffmpeg library is not installed. Please install ffmpeg and try again.")
        return

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
    speaker_queue = queue.Queue()
    mic_queue = queue.Queue()

    user_audio_recorder = AudioRecorder.DefaultMicRecorder(device_index=mic_device_index)
    user_audio_recorder.record_into_queue(mic_queue)

    time.sleep(2)

    speaker_audio_recorder = AudioRecorder.DefaultSpeakerRecorder(device_index=speaker_device_index)
    speaker_audio_recorder.record_into_queue(speaker_queue)

    model = TranscriberModels.get_model()

    transcriber = AudioTranscriber(user_audio_recorder.source, speaker_audio_recorder.source, model)
    transcribe = threading.Thread(target=transcriber.transcribe_audio_queue, args=(speaker_queue, mic_queue))
    transcribe.daemon = True
    transcribe.start()

    transcript_textbox, suggestion_textbox = create_ui_components(root, transcriber, speaker_queue, mic_queue, llm_client)

    print("READY")

    if llm_client:
        update_transcript_UI(transcriber, transcript_textbox, suggestion_textbox, llm_client)
    else:
        def update_transcript_no_llm():
            transcript_string = transcriber.get_transcript()
            write_in_textbox(transcript_textbox, transcript_string)
            transcript_textbox.after(300, update_transcript_no_llm)
        update_transcript_no_llm()

    root.mainloop()

if __name__ == "__main__":
    main()