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

        self.root.title("Ecoute")
        self.root.geometry("900x850")

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
        # Premium typography
        title_font = ("Segoe UI", 32, "bold")
        subtitle_font = ("Segoe UI", 15)
        header_font = ("Segoe UI", 18, "bold")
        label_font = ("Segoe UI", 14)
        input_font = ("Segoe UI", 15)

        # Premium color palette
        bg_dark = "#0F172A"  # Deep navy background
        card_bg = "#1E293B"  # Card background
        input_bg = "#334155"  # Input field background
        input_border = "#475569"  # Subtle border
        text_primary = "#F8FAFC"  # Pure white text
        text_secondary = "#CBD5E1"  # Light grey text
        text_muted = "#94A3B8"  # Muted grey
        accent_blue = "#2563EB"  # Vibrant blue
        accent_blue_hover = "#1D4ED8"  # Darker blue on hover

        self.root.configure(fg_color=bg_dark)

        # Main scrollable container with generous padding
        main_frame = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=60, pady=50)
        main_frame.grid_columnconfigure(0, weight=1)

        # Hero section with title and subtitle
        hero_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hero_frame.grid(row=0, column=0, sticky="ew", pady=(0, 40))
        hero_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            hero_frame,
            text="AI Copilot",
            font=title_font,
            text_color=text_primary
        )
        title_label.grid(row=0, column=0, pady=(0, 10))

        subtitle_label = ctk.CTkLabel(
            hero_frame,
            text="Your intelligent assistant for live interviews",
            font=subtitle_font,
            text_color=text_muted
        )
        subtitle_label.grid(row=1, column=0)

        # Card 1: Audio Setup
        audio_card = ctk.CTkFrame(main_frame, fg_color=card_bg, corner_radius=16)
        audio_card.grid(row=1, column=0, sticky="ew", pady=(0, 24))
        audio_card.grid_columnconfigure(1, weight=1)

        audio_header = ctk.CTkLabel(
            audio_card,
            text="🎙️  Audio Configuration",
            font=header_font,
            text_color=text_primary,
            anchor="w"
        )
        audio_header.grid(row=0, column=0, columnspan=2, padx=30, pady=(25, 20), sticky="w")

        # Microphone section
        mic_label = ctk.CTkLabel(
            audio_card,
            text="Microphone Input",
            font=label_font,
            text_color=text_secondary,
            anchor="w"
        )
        mic_label.grid(row=1, column=0, padx=30, pady=(10, 8), sticky="w")

        self.mic_dropdown = ctk.CTkComboBox(
            audio_card,
            values=["Scanning devices..."],
            font=input_font,
            fg_color=input_bg,
            border_color=input_border,
            button_color=input_border,
            button_hover_color=accent_blue,
            dropdown_fg_color=card_bg,
            dropdown_hover_color=input_bg,
            text_color=text_primary,
            state="readonly",
            corner_radius=10,
            height=45
        )
        self.mic_dropdown.grid(row=2, column=0, columnspan=2, padx=30, pady=(0, 20), sticky="ew")

        # Speaker section
        speaker_label = ctk.CTkLabel(
            audio_card,
            text="Speaker Output (for capturing interviewer)",
            font=label_font,
            text_color=text_secondary,
            anchor="w"
        )
        speaker_label.grid(row=3, column=0, padx=30, pady=(10, 8), sticky="w")

        self.speaker_dropdown = ctk.CTkComboBox(
            audio_card,
            values=["Scanning devices..."],
            font=input_font,
            fg_color=input_bg,
            border_color=input_border,
            button_color=input_border,
            button_hover_color=accent_blue,
            dropdown_fg_color=card_bg,
            dropdown_hover_color=input_bg,
            text_color=text_primary,
            state="readonly",
            corner_radius=10,
            height=45
        )
        self.speaker_dropdown.grid(row=4, column=0, columnspan=2, padx=30, pady=(0, 25), sticky="ew")

        # Card 2: API Configuration
        api_card = ctk.CTkFrame(main_frame, fg_color=card_bg, corner_radius=16)
        api_card.grid(row=2, column=0, sticky="ew", pady=(0, 24))
        api_card.grid_columnconfigure(1, weight=1)

        api_header = ctk.CTkLabel(
            api_card,
            text="🔑  API Configuration",
            font=header_font,
            text_color=text_primary,
            anchor="w"
        )
        api_header.grid(row=0, column=0, columnspan=2, padx=30, pady=(25, 20), sticky="w")

        # Groq API Key
        groq_label = ctk.CTkLabel(
            api_card,
            text="Groq API Key (Audio Transcription)",
            font=label_font,
            text_color=text_secondary,
            anchor="w"
        )
        groq_label.grid(row=1, column=0, padx=30, pady=(10, 8), sticky="w")

        self.groq_api_key_entry = ctk.CTkEntry(
            api_card,
            placeholder_text="gsk_...",
            font=input_font,
            fg_color=input_bg,
            border_color=input_border,
            text_color=text_primary,
            placeholder_text_color=text_muted,
            show="•",
            corner_radius=10,
            height=45,
            border_width=2
        )
        existing_groq_key = os.getenv("GROQ_API_KEY", "")
        if existing_groq_key:
            self.groq_api_key_entry.insert(0, existing_groq_key)
        self.groq_api_key_entry.grid(row=2, column=0, columnspan=2, padx=30, pady=(0, 15), sticky="ew")

        # Local LM Studio info banner
        info_banner = ctk.CTkFrame(api_card, fg_color=input_bg, corner_radius=10)
        info_banner.grid(row=3, column=0, columnspan=2, padx=30, pady=(5, 25), sticky="ew")

        info_label = ctk.CTkLabel(
            info_banner,
            text="ℹ️  AI suggestions powered by local LM Studio server (http://127.0.0.1:1234)",
            font=("Segoe UI", 13),
            text_color=text_muted,
            anchor="w"
        )
        info_label.pack(padx=20, pady=15, fill="x")

        # Card 3: Interview Context
        context_card = ctk.CTkFrame(main_frame, fg_color=card_bg, corner_radius=16)
        context_card.grid(row=3, column=0, sticky="ew", pady=(0, 30))
        context_card.grid_columnconfigure(0, weight=1)

        context_header = ctk.CTkLabel(
            context_card,
            text="📄  Interview Context",
            font=header_font,
            text_color=text_primary,
            anchor="w"
        )
        context_header.grid(row=0, column=0, padx=30, pady=(25, 10), sticky="w")

        context_subtitle = ctk.CTkLabel(
            context_card,
            text="Paste your resume, job description, or any relevant background information",
            font=("Segoe UI", 13),
            text_color=text_muted,
            anchor="w"
        )
        context_subtitle.grid(row=1, column=0, padx=30, pady=(0, 15), sticky="w")

        self.context_textbox = ctk.CTkTextbox(
            context_card,
            font=("Segoe UI", 14),
            fg_color=input_bg,
            text_color=text_secondary,
            border_width=2,
            border_color=input_border,
            corner_radius=10,
            wrap="word",
            height=200,
            spacing1=5,
            spacing3=5
        )
        self.context_textbox.grid(row=2, column=0, padx=30, pady=(0, 25), sticky="ew")

        if os.path.exists("temp_context.txt"):
            try:
                with open("temp_context.txt", "r", encoding="utf-8") as f:
                    self.context_textbox.insert("0.0", f.read())
            except:
                pass

        # Launch button - big, bold, prominent
        self.start_button = ctk.CTkButton(
            main_frame,
            text="Launch Copilot",
            font=("Segoe UI", 18, "bold"),
            height=60,
            corner_radius=12,
            fg_color=accent_blue,
            hover_color=accent_blue_hover,
            text_color=text_primary,
            command=self.start_application
        )
        self.start_button.grid(row=4, column=0, pady=(10, 20), sticky="ew")

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

        if mic_selection == "Scanning devices..." or speaker_selection == "Scanning devices...":
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

        self.root.destroy()

        try:
            import main
            main.main()
        except Exception as e:
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
