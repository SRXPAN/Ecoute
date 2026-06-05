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

# Глобальний прапорець для відстеження статусу генерації
is_generating = False

def write_in_textbox(textbox, text):
    textbox.delete("0.0", "end")
    textbox.insert("0.0", text)

def update_transcript_UI(transcriber, transcript_textbox, suggestion_textbox, llm_client, overlay_manager, status_label):
    global is_generating

    # 1. Оновлюємо текст статусів у реальному часі!
    current_statuses = transcriber.get_statuses()
    status_label.configure(text=current_statuses)

    # 2. Оновлюємо транскрипт
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

    transcript_textbox.after(300, update_transcript_UI, transcriber, transcript_textbox, suggestion_textbox, llm_client, overlay_manager, status_label)

def get_ai_suggestion(interviewer_question, suggestion_textbox, llm_client, overlay_manager):
    try:
        suggestion_textbox.delete("0.0", "end")
        suggestion_textbox.insert("0.0", "🤔 Thinking...\n")

        full_response = ""
        response_generator = llm_client.get_suggestion(interviewer_question)

        # 1. Очищаємо оверлей перед початком нової відповіді
        overlay_manager.update_suggestions("", clear=True)

        # 2. Стрімимо токени одночасно і в головне вікно, і в оверлей
        for token in response_generator:
            full_response += token

            # Оновлюємо дашборд
            suggestion_textbox.delete("0.0", "end")
            suggestion_textbox.insert("0.0", full_response)
            suggestion_textbox.update()

            # Миттєво відправляємо шматок тексту в оверлей
            overlay_manager.update_suggestions(token, clear=False)

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
    root.title("AI Interview Copilot - Dashboard")
    root.geometry("1400x800")
    root.configure(fg_color="#0F172A")

    root.grid_columnconfigure(0, weight=3)
    root.grid_columnconfigure(1, weight=2)
    root.grid_rowconfigure(0, weight=1)

    modern_font = ("Segoe UI", 15)
    title_font = ("Segoe UI", 18, "bold")

    left_frame = ctk.CTkFrame(root, fg_color="#1E293B", corner_radius=12)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
    left_frame.grid_columnconfigure(0, weight=1)
    left_frame.grid_rowconfigure(1, weight=1)

    # Контейнер для заголовка та статусів
    header_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
    header_frame.grid_columnconfigure(1, weight=1)

    transcript_label = ctk.CTkLabel(header_frame, text="📝 Live Transcript", font=title_font, text_color="#F8FAFC")
    transcript_label.grid(row=0, column=0, sticky="w")

    # НОВИЙ ІНДИКАТОР СТАТУСУ
    status_label = ctk.CTkLabel(header_frame, text="Mic: 🟢 Idle  |  Speaker: 🟢 Idle", font=("Segoe UI", 13, "bold"), text_color="#9CA3AF")
    status_label.grid(row=0, column=1, sticky="e")

    transcript_textbox = ctk.CTkTextbox(
        left_frame, font=modern_font, text_color="#CBD5E1", fg_color="#0F172A",
        border_width=1, border_color="#334155", wrap="word", spacing1=5
    )
    transcript_textbox.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

    clear_button = ctk.CTkButton(
        left_frame, text="Clear Session", font=("Segoe UI", 14), height=40, corner_radius=8,
        fg_color="#334155", hover_color="#475569", text_color="#F8FAFC",
        command=lambda: clear_context(transcriber, None, llm_client, overlay_manager) # FIX None error
    )
    clear_button.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

    right_frame = ctk.CTkFrame(root, fg_color="#1E293B", corner_radius=12)
    right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
    right_frame.grid_columnconfigure(0, weight=1)
    right_frame.grid_rowconfigure(1, weight=1)

    suggestion_label = ctk.CTkLabel(right_frame, text="💡 AI Copilot", font=title_font, text_color="#38BDF8")
    suggestion_label.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))

    suggestion_textbox = ctk.CTkTextbox(
        right_frame, font=("Segoe UI", 16), text_color="#38BDF8", fg_color="#0F172A",
        border_width=1, border_color="#334155", wrap="word", spacing1=8
    )
    suggestion_textbox.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
    suggestion_textbox.insert("0.0", "Waiting for the first question...")

    toggle_overlay_button = ctk.CTkButton(
        right_frame, text="Toggle Stealth Overlay", font=("Segoe UI", 14, "bold"), height=40, corner_radius=8,
        fg_color="#0EA5E9", hover_color="#0284C7", text_color="#FFFFFF",
        command=overlay_manager.toggle_visibility
    )
    toggle_overlay_button.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

    # Виправляємо лямбду для clear_button
    clear_button.configure(command=lambda: clear_context(transcriber, suggestion_textbox, llm_client, overlay_manager))

    return transcript_textbox, suggestion_textbox, status_label

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
        llm_client = LLMClient(provider="local")
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

    # Hard exit function to kill all threads and process
    def hard_exit():
        print("[INFO] Initiating hard exit...")
        cleanup_on_exit()
        try:
            transcriber.close()
        except:
            pass
        os._exit(0)  # Immediately terminates all threads and the process

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

        # Register hard exit function
        root.protocol("WM_DELETE_WINDOW", hard_exit)

        transcript_textbox, suggestion_textbox, status_label = create_ui_components(root, transcriber, llm_client, overlay_manager)

        print("READY")

        if llm_client:
            update_transcript_UI(transcriber, transcript_textbox, suggestion_textbox, llm_client, overlay_manager, status_label)
        else:
            def update_transcript_no_llm():
                transcript_string = transcriber.get_transcript()
                write_in_textbox(transcript_textbox, transcript_textbox)
                transcript_textbox.after(300, update_transcript_no_llm)
            update_transcript_no_llm()

        root.mainloop()

    except Exception as e:
        print(f"[ERROR] Failed to initialize audio system: {e}")

        # Register cleanup for error case
        root.protocol("WM_DELETE_WINDOW", lambda: (cleanup_on_exit(), os._exit(0)))

        # Create minimal UI to show error
        transcript_textbox, suggestion_textbox = create_ui_components(root, None, llm_client, overlay_manager)

        error_message = f"❌ Audio Initialization Failed\n\n{str(e)}\n\nPossible causes:\n• Invalid audio device selected\n• Audio device disconnected\n• Sample rate not supported\n\nPlease restart and select different audio devices."
        write_in_textbox(transcript_textbox, error_message)
        write_in_textbox(suggestion_textbox, "Audio system unavailable")

        root.mainloop()

if __name__ == "__main__":
    main()