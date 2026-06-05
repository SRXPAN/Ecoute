import customtkinter as ctk
import sounddevice as sd
import pyaudiowpatch as pyaudio
from tkinter import messagebox
import os
from dotenv import load_dotenv, set_key

class LauncherApp:
    def __init__(self):
        load_dotenv()

        self.root = ctk.CTk()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root.title("AI Interview Copilot Launcher")
        self.root.geometry("800x750")

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.mic_devices = []
        self.speaker_devices = []

        self.create_ui()
        self.scan_audio_devices()

    def scan_audio_devices(self):
        try:
            with pyaudio.PyAudio() as p:
                wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)

                self.mic_devices = []
                self.speaker_devices = []

                for i in range(p.get_device_count()):
                    device_info = p.get_device_info_by_index(i)

                    if device_info["maxInputChannels"] > 0 and not device_info.get("isLoopbackDevice", False):
                        self.mic_devices.append({
                            "index": i,
                            "name": device_info["name"]
                        })

                for loopback in p.get_loopback_device_info_generator():
                    self.speaker_devices.append({
                        "index": loopback["index"],
                        "name": loopback["name"]
                    })

                default_output_device = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
                for speaker in self.speaker_devices:
                    if default_output_device["name"] in speaker["name"]:
                        speaker["name"] += " (Default)"
                        break

                default_input_device = p.get_device_info_by_index(wasapi_info["defaultInputDevice"])
                for mic in self.mic_devices:
                    if mic["index"] == default_input_device["index"]:
                        mic["name"] += " (Default)"
                        break

            mic_names = [device["name"] for device in self.mic_devices]
            speaker_names = [device["name"] for device in self.speaker_devices]

            self.mic_dropdown.configure(values=mic_names)
            self.speaker_dropdown.configure(values=speaker_names)

            if mic_names:
                default_mic = next((name for name in mic_names if "(Default)" in name), mic_names[0])
                self.mic_dropdown.set(default_mic)

            if speaker_names:
                default_speaker = next((name for name in speaker_names if "(Default)" in name), speaker_names[0])
                self.speaker_dropdown.set(default_speaker)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan audio devices: {str(e)}")

    def create_ui(self):
        modern_font = ("Segoe UI", 14)
        title_font = ("Segoe UI", 24, "bold")
        header_font = ("Segoe UI", 16, "bold")

        self.root.configure(fg_color="#111827")

        main_frame = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        main_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            main_frame,
            text="AI Interview Copilot",
            font=title_font,
            text_color="#F9FAFB"
        )
        title_label.grid(row=0, column=0, pady=(0, 30), sticky="w")

        # Card 1: Audio Setup
        audio_section = ctk.CTkFrame(main_frame, fg_color="#1F2937", corner_radius=12)
        audio_section.grid(row=1, column=0, sticky="ew", pady=(0, 20), ipady=10)
        audio_section.grid_columnconfigure(1, weight=1)

        audio_title = ctk.CTkLabel(audio_section, text="🎙️ Audio Setup", font=header_font, text_color="#E5E7EB")
        audio_title.grid(row=0, column=0, columnspan=2, pady=(15, 15), padx=20, sticky="w")

        mic_label = ctk.CTkLabel(audio_section, text="Microphone:", font=modern_font, text_color="#9CA3AF")
        mic_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.mic_dropdown = ctk.CTkComboBox(audio_section, values=["Scanning..."], width=400, font=modern_font, fg_color="#374151", border_width=0, button_color="#4B5563", state="readonly")
        self.mic_dropdown.grid(row=1, column=1, padx=20, pady=10, sticky="ew")

        speaker_label = ctk.CTkLabel(audio_section, text="Speakers:", font=modern_font, text_color="#9CA3AF")
        speaker_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.speaker_dropdown = ctk.CTkComboBox(audio_section, values=["Scanning..."], width=400, font=modern_font, fg_color="#374151", border_width=0, button_color="#4B5563", state="readonly")
        self.speaker_dropdown.grid(row=2, column=1, padx=20, pady=(10, 15), sticky="ew")

        # Card 2: API Credentials (Only Groq for transcription)
        llm_section = ctk.CTkFrame(main_frame, fg_color="#1F2937", corner_radius=12)
        llm_section.grid(row=2, column=0, sticky="ew", pady=(0, 20), ipady=10)
        llm_section.grid_columnconfigure(1, weight=1)

        llm_title = ctk.CTkLabel(llm_section, text="🔑 API Credentials", font=header_font, text_color="#E5E7EB")
        llm_title.grid(row=0, column=0, columnspan=2, pady=(15, 15), padx=20, sticky="w")

        groq_label = ctk.CTkLabel(llm_section, text="Groq API Key (Transcription):", font=modern_font, text_color="#9CA3AF")
        groq_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.groq_api_key_entry = ctk.CTkEntry(llm_section, width=400, show="•", font=modern_font, fg_color="#374151", border_width=0, placeholder_text="gsk_...")
        existing_groq_key = os.getenv("GROQ_API_KEY", "")
        if existing_groq_key: self.groq_api_key_entry.insert(0, existing_groq_key)
        self.groq_api_key_entry.grid(row=1, column=1, padx=20, pady=(10, 15), sticky="ew")

        # Info label about local LM Studio
        info_label = ctk.CTkLabel(
            llm_section,
            text="ℹ️ AI suggestions powered by local LM Studio (http://127.0.0.1:1234)",
            font=("Segoe UI", 12),
            text_color="#6B7280"
        )
        info_label.grid(row=2, column=0, columnspan=2, padx=20, pady=(5, 15), sticky="w")

        # Card 3: Interview Context
        context_section = ctk.CTkFrame(main_frame, fg_color="#1F2937", corner_radius=12)
        context_section.grid(row=3, column=0, sticky="ew", pady=(0, 30))
        context_section.grid_columnconfigure(0, weight=1)

        context_title = ctk.CTkLabel(context_section, text="📄 Interview Context (Resume / Job Description)", font=header_font, text_color="#E5E7EB")
        context_title.grid(row=0, column=0, pady=(15, 10), padx=20, sticky="w")

        self.context_textbox = ctk.CTkTextbox(context_section, height=180, font=("Segoe UI", 13), fg_color="#111827", text_color="#D1D5DB", border_width=1, border_color="#374151", wrap="word")
        self.context_textbox.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")

        if os.path.exists("temp_context.txt"):
            try:
                with open("temp_context.txt", "r", encoding="utf-8") as f:
                    self.context_textbox.insert("0.0", f.read())
            except: pass

        # Launch Button
        self.start_button = ctk.CTkButton(
            main_frame, text="Launch Copilot", font=("Segoe UI", 16, "bold"), height=50, corner_radius=8,
            fg_color="#2563EB", hover_color="#1D4ED8", command=self.start_application
        )
        self.start_button.grid(row=4, column=0, pady=(0, 20), sticky="ew")

    def start_application(self):
        groq_api_key = self.groq_api_key_entry.get().strip()

        if not groq_api_key:
            messagebox.showerror("Error", "Please enter your Groq API key for transcription")
            return

        context_text = self.context_textbox.get("0.0", "end-1c").strip()
        if not context_text:
            response = messagebox.askyesno(
                "Warning",
                "No interview context provided. The AI assistant will provide generic responses. Continue anyway?"
            )
            if not response:
                return

        mic_selection = self.mic_dropdown.get()
        speaker_selection = self.speaker_dropdown.get()

        if mic_selection == "Scanning..." or speaker_selection == "Scanning...":
            messagebox.showerror("Error", "Audio devices are still scanning. Please wait.")
            return

        mic_index = None
        for device in self.mic_devices:
            if device["name"] == mic_selection:
                mic_index = device["index"]
                break

        speaker_index = None
        for device in self.speaker_devices:
            if device["name"] == speaker_selection:
                speaker_index = device["index"]
                break

        if mic_index is None or speaker_index is None:
            messagebox.showerror("Error", "Failed to get audio device indices")
            return

        env_file = ".env"
        if not os.path.exists(env_file):
            with open(env_file, "w") as f:
                f.write("")

        set_key(env_file, "GROQ_API_KEY", groq_api_key)
        set_key(env_file, "MIC_DEVICE_INDEX", str(mic_index))
        set_key(env_file, "SPEAKER_DEVICE_INDEX", str(speaker_index))

        with open("temp_context.txt", "w", encoding="utf-8") as f:
            f.write(context_text)

        # Destroy launcher window completely to avoid Tkinter conflicts
        self.root.destroy()

        try:
            # Import and run main application directly (PyInstaller compatible)
            import main
            main.main()
        except Exception as e:
            # Create new temporary root for error message since original is destroyed
            import tkinter as tk
            err_root = tk.Tk()
            err_root.withdraw()
            messagebox.showerror("Error", f"Failed to start main application: {str(e)}")
            err_root.destroy()
            return

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LauncherApp()
    app.run()
