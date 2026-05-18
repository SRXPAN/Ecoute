import customtkinter as ctk
import sounddevice as sd
import pyaudiowpatch as pyaudio
from tkinter import messagebox
import os
from dotenv import load_dotenv, set_key
import subprocess
import sys

class LauncherApp:
    def __init__(self):
        load_dotenv()

        self.root = ctk.CTk()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root.title("AI Interview Copilot - Configuration")
        self.root.geometry("800x700")

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
        main_frame = ctk.CTkScrollableFrame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            main_frame,
            text="AI Interview Copilot Configuration",
            font=("Arial", 24, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20), sticky="w")

        audio_section = ctk.CTkFrame(main_frame)
        audio_section.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        audio_section.grid_columnconfigure(1, weight=1)

        audio_title = ctk.CTkLabel(
            audio_section,
            text="Audio Devices",
            font=("Arial", 18, "bold")
        )
        audio_title.grid(row=0, column=0, columnspan=2, pady=(10, 15), padx=10, sticky="w")

        mic_label = ctk.CTkLabel(audio_section, text="Microphone Input:", font=("Arial", 14))
        mic_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.mic_dropdown = ctk.CTkComboBox(
            audio_section,
            values=["Scanning..."],
            width=400,
            state="readonly"
        )
        self.mic_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        speaker_label = ctk.CTkLabel(audio_section, text="Speaker Output:", font=("Arial", 14))
        speaker_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.speaker_dropdown = ctk.CTkComboBox(
            audio_section,
            values=["Scanning..."],
            width=400,
            state="readonly"
        )
        self.speaker_dropdown.grid(row=2, column=1, padx=10, pady=(5, 10), sticky="ew")

        llm_section = ctk.CTkFrame(main_frame)
        llm_section.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        llm_section.grid_columnconfigure(1, weight=1)

        llm_title = ctk.CTkLabel(
            llm_section,
            text="LLM Configuration",
            font=("Arial", 18, "bold")
        )
        llm_title.grid(row=0, column=0, columnspan=2, pady=(10, 15), padx=10, sticky="w")

        provider_label = ctk.CTkLabel(llm_section, text="Provider:", font=("Arial", 14))
        provider_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.provider_dropdown = ctk.CTkComboBox(
            llm_section,
            values=["Groq (Whisper)", "OpenAI (Future)", "Gemini (Future)"],
            width=400,
            state="readonly"
        )
        self.provider_dropdown.set("Groq (Whisper)")
        self.provider_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        api_key_label = ctk.CTkLabel(llm_section, text="API Key:", font=("Arial", 14))
        api_key_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.api_key_entry = ctk.CTkEntry(
            llm_section,
            width=400,
            show="*",
            placeholder_text="Enter your Groq API key"
        )
        existing_key = os.getenv("GROQ_API_KEY", "")
        if existing_key:
            self.api_key_entry.insert(0, existing_key)
        self.api_key_entry.grid(row=2, column=1, padx=10, pady=(5, 10), sticky="ew")

        context_section = ctk.CTkFrame(main_frame)
        context_section.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        context_section.grid_columnconfigure(0, weight=1)

        context_title = ctk.CTkLabel(
            context_section,
            text="Interview Context (Resume / Job Description)",
            font=("Arial", 18, "bold")
        )
        context_title.grid(row=0, column=0, pady=(10, 10), padx=10, sticky="w")

        self.context_textbox = ctk.CTkTextbox(
            context_section,
            height=200,
            font=("Arial", 12),
            wrap="word"
        )
        self.context_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        existing_context = ""
        if os.path.exists("temp_context.txt"):
            try:
                with open("temp_context.txt", "r", encoding="utf-8") as f:
                    existing_context = f.read()
                self.context_textbox.insert("0.0", existing_context)
            except:
                pass

        self.start_button = ctk.CTkButton(
            main_frame,
            text="START",
            font=("Arial", 20, "bold"),
            height=50,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self.start_application
        )
        self.start_button.grid(row=4, column=0, pady=(10, 0), sticky="ew")

    def start_application(self):
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your API key")
            return

        context_text = self.context_textbox.get("0.0", "end-1c").strip()
        if not context_text:
            response = messagebox.askyesno(
                "Warning",
                "No interview context provided. Continue anyway?"
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

        set_key(env_file, "GROQ_API_KEY", api_key)
        set_key(env_file, "MIC_DEVICE_INDEX", str(mic_index))
        set_key(env_file, "SPEAKER_DEVICE_INDEX", str(speaker_index))

        with open("temp_context.txt", "w", encoding="utf-8") as f:
            f.write(context_text)

        self.root.withdraw()

        try:
            subprocess.run([sys.executable, "main.py"], check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to start main application: {str(e)}")
            self.root.deiconify()
            return
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            self.root.deiconify()
            return

        self.root.quit()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LauncherApp()
    app.run()
