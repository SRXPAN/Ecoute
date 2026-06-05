import customtkinter as ctk
import sounddevice as sd
import pyaudiowpatch as pyaudio
from tkinter import messagebox
import os
import json
from dotenv import load_dotenv, set_key

class LauncherApp:
    def __init__(self):
        load_dotenv()

        self.root = ctk.CTk()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root.title("AI Copilot Pro - Launcher")
        self.root.geometry("1000x1000")

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.speaker_devices = []
        self.profiles = self.load_profiles()
        self.selected_persona = ctk.StringVar(value="Short Bullets")

        self.create_ui()
        self.scan_audio_devices()

        # Load default profile if available
        if "Default - EdTech PM" in self.profiles:
            self.load_profile("Default - EdTech PM")

    def load_profiles(self):
        """Load saved profiles from profiles.json"""
        if os.path.exists("profiles.json"):
            try:
                with open("profiles.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARNING] Failed to load profiles.json: {e}")
                return self.get_default_profiles()
        return self.get_default_profiles()

    def get_default_profiles(self):
        """Return default profiles structure"""
        return {
            "Default - EdTech PM": {
                "context": "Role: Junior Project/Product Manager.\nProject: Creator and manager of e-learn.space MVP.\nExperience: Managed full SDLC from requirements to launch using Agile/Scrum.\nSkills: C++, JS, React Native, Unreal Engine 5.\nLanguages: Ukrainian (Native), English (B2/C1), Polish (B2).",
                "persona": "Short Bullets"
            }
        }

    def save_profiles(self):
        """Save profiles to profiles.json"""
        try:
            with open("profiles.json", "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
            print("[INFO] Profiles saved to profiles.json")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profiles: {str(e)}")

    def load_profile(self, profile_name):
        """Load a profile into the context textbox and set persona"""
        if profile_name and profile_name in self.profiles:
            profile_data = self.profiles[profile_name]

            # Load context
            self.context_textbox.delete("0.0", "end")
            self.context_textbox.insert("0.0", profile_data["context"])

            # Load persona
            persona = profile_data.get("persona", "Short Bullets")
            self.selected_persona.set(persona)

            print(f"[INFO] Loaded profile: {profile_name}")

    def save_current_profile(self):
        """Save current context and persona as a new profile"""
        profile_name = self.profile_name_entry.get().strip()
        if not profile_name:
            messagebox.showerror("Error", "Please enter a profile name")
            return

        context_text = self.context_textbox.get("0.0", "end-1c").strip()
        if not context_text:
            messagebox.showerror("Error", "Context is empty")
            return

        # Save profile with context and persona
        self.profiles[profile_name] = {
            "context": context_text,
            "persona": self.selected_persona.get()
        }

        self.save_profiles()

        # Update dropdown
        profile_names = list(self.profiles.keys())
        self.profile_dropdown.configure(values=profile_names)
        self.profile_dropdown.set(profile_name)

        messagebox.showinfo("Success", f"Profile '{profile_name}' saved!")

    def delete_current_profile(self):
        """Delete the selected profile"""
        selected_profile = self.profile_dropdown.get()

        if not selected_profile or selected_profile not in self.profiles:
            messagebox.showerror("Error", "No profile selected")
            return

        if selected_profile == "Default - EdTech PM":
            messagebox.showerror("Error", "Cannot delete default profile")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Delete profile '{selected_profile}'?")
        if confirm:
            del self.profiles[selected_profile]
            self.save_profiles()

            # Update dropdown
            profile_names = list(self.profiles.keys())
            self.profile_dropdown.configure(values=profile_names)
            if profile_names:
                self.profile_dropdown.set(profile_names[0])
                self.load_profile(profile_names[0])

            messagebox.showinfo("Success", f"Profile '{selected_profile}' deleted")

    def scan_audio_devices(self):
        try:
            with pyaudio.PyAudio() as p:
                wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)

                self.speaker_devices = []

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

            speaker_names = [device["name"] for device in self.speaker_devices]

            self.speaker_dropdown.configure(values=speaker_names)

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
        bg_dark = "#0F172A"
        card_bg = "#1E293B"
        input_bg = "#334155"
        input_border = "#475569"
        text_primary = "#F8FAFC"
        text_secondary = "#CBD5E1"
        text_muted = "#94A3B8"
        accent_blue = "#2563EB"
        accent_blue_hover = "#1D4ED8"
        accent_purple = "#8B5CF6"
        accent_red = "#EF4444"

        self.root.configure(fg_color=bg_dark)

        # Main scrollable container
        main_frame = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=60, pady=50)
        main_frame.grid_columnconfigure(0, weight=1)

        # Hero section
        hero_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hero_frame.grid(row=0, column=0, sticky="ew", pady=(0, 40))
        hero_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            hero_frame,
            text="AI Copilot Pro",
            font=title_font,
            text_color=text_primary
        )
        title_label.grid(row=0, column=0, pady=(0, 10))

        subtitle_label = ctk.CTkLabel(
            hero_frame,
            text="Premium interview assistant with profiles, personas, and advanced automation",
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

        speaker_label = ctk.CTkLabel(
            audio_card,
            text="Speaker Output (for capturing interviewer)",
            font=label_font,
            text_color=text_secondary,
            anchor="w"
        )
        speaker_label.grid(row=1, column=0, padx=30, pady=(10, 8), sticky="w")

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
        self.speaker_dropdown.grid(row=2, column=0, columnspan=2, padx=30, pady=(0, 25), sticky="ew")

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

        # Card 3: Profile Management
        profile_card = ctk.CTkFrame(main_frame, fg_color=card_bg, corner_radius=16)
        profile_card.grid(row=3, column=0, sticky="ew", pady=(0, 24))
        profile_card.grid_columnconfigure(1, weight=1)

        profile_header = ctk.CTkLabel(
            profile_card,
            text="👤  Profile Management",
            font=header_font,
            text_color=text_primary,
            anchor="w"
        )
        profile_header.grid(row=0, column=0, columnspan=3, padx=30, pady=(25, 10), sticky="w")

        profile_subtitle = ctk.CTkLabel(
            profile_card,
            text="Save and load interview context profiles with AI persona settings",
            font=("Segoe UI", 13),
            text_color=text_muted,
            anchor="w"
        )
        profile_subtitle.grid(row=1, column=0, columnspan=3, padx=30, pady=(0, 20), sticky="w")

        # Profile dropdown
        profile_label = ctk.CTkLabel(
            profile_card,
            text="Select Profile:",
            font=label_font,
            text_color=text_secondary,
            anchor="w"
        )
        profile_label.grid(row=2, column=0, padx=30, pady=(0, 8), sticky="w")

        profile_names = list(self.profiles.keys())
        self.profile_dropdown = ctk.CTkOptionMenu(
            profile_card,
            values=profile_names,
            font=input_font,
            fg_color=input_bg,
            button_color=input_border,
            button_hover_color=accent_blue,
            dropdown_fg_color=card_bg,
            text_color=text_primary,
            corner_radius=10,
            height=40,
            command=lambda choice: self.load_profile(choice)
        )
        self.profile_dropdown.grid(row=2, column=1, columnspan=2, padx=10, pady=(0, 8), sticky="ew")

        # New profile name entry
        new_profile_label = ctk.CTkLabel(
            profile_card,
            text="New Profile Name:",
            font=label_font,
            text_color=text_secondary,
            anchor="w"
        )
        new_profile_label.grid(row=3, column=0, padx=30, pady=(10, 8), sticky="w")

        self.profile_name_entry = ctk.CTkEntry(
            profile_card,
            placeholder_text="e.g., Backend Engineer",
            font=input_font,
            fg_color=input_bg,
            border_color=input_border,
            text_color=text_primary,
            corner_radius=10,
            height=40
        )
        self.profile_name_entry.grid(row=3, column=1, padx=10, pady=(10, 8), sticky="ew")

        # Action buttons
        buttons_frame = ctk.CTkFrame(profile_card, fg_color="transparent")
        buttons_frame.grid(row=3, column=2, padx=(10, 30), pady=(10, 8), sticky="ew")

        save_profile_btn = ctk.CTkButton(
            buttons_frame,
            text="💾 Save",
            font=("Segoe UI", 14, "bold"),
            width=80,
            height=40,
            corner_radius=10,
            fg_color=accent_purple,
            hover_color="#7C3AED",
            text_color=text_primary,
            command=self.save_current_profile
        )
        save_profile_btn.pack(side="left", padx=2)

        delete_profile_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Delete",
            font=("Segoe UI", 14, "bold"),
            width=80,
            height=40,
            corner_radius=10,
            fg_color=accent_red,
            hover_color="#DC2626",
            text_color=text_primary,
            command=self.delete_current_profile
        )
        delete_profile_btn.pack(side="left", padx=2)

        # Add spacing
        ctk.CTkLabel(profile_card, text="", height=10).grid(row=4, column=0)

        # Card 4: AI Persona Selection
        persona_card = ctk.CTkFrame(main_frame, fg_color=card_bg, corner_radius=16)
        persona_card.grid(row=4, column=0, sticky="ew", pady=(0, 24))
        persona_card.grid_columnconfigure(0, weight=1)

        persona_header = ctk.CTkLabel(
            persona_card,
            text="🎭  AI Persona",
            font=header_font,
            text_color=text_primary,
            anchor="w"
        )
        persona_header.grid(row=0, column=0, padx=30, pady=(25, 10), sticky="w")

        persona_subtitle = ctk.CTkLabel(
            persona_card,
            text="Choose how the AI formats responses",
            font=("Segoe UI", 13),
            text_color=text_muted,
            anchor="w"
        )
        persona_subtitle.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")

        personas = [
            ("Short Bullets", "Concise bullet points (max 3, highly focused)"),
            ("Technical Deep Dive", "Detailed technical architecture and SDLC focus"),
            ("STAR Method", "Situation, Task, Action, Result format")
        ]

        for i, (persona_name, persona_desc) in enumerate(personas):
            radio = ctk.CTkRadioButton(
                persona_card,
                text=f"{persona_name}\n{persona_desc}",
                variable=self.selected_persona,
                value=persona_name,
                font=("Segoe UI", 14),
                text_color=text_secondary,
                fg_color=accent_purple,
                hover_color=accent_blue
            )
            radio.grid(row=2+i, column=0, padx=50, pady=8, sticky="w")

        # Add spacing
        ctk.CTkLabel(persona_card, text="", height=10).grid(row=5, column=0)

        # Card 5: Interview Context
        context_card = ctk.CTkFrame(main_frame, fg_color=card_bg, corner_radius=16)
        context_card.grid(row=5, column=0, sticky="ew", pady=(0, 30))
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
            text="Your resume, skills, and project experience",
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

        # Launch button
        self.start_button = ctk.CTkButton(
            main_frame,
            text="🚀 Launch Copilot Pro",
            font=("Segoe UI", 20, "bold"),
            height=65,
            corner_radius=12,
            fg_color=accent_blue,
            hover_color=accent_blue_hover,
            text_color=text_primary,
            command=self.start_application
        )
        self.start_button.grid(row=6, column=0, pady=(10, 15), sticky="ew")

        # Hotkey tips banner
        tips_frame = ctk.CTkFrame(main_frame, fg_color=input_bg, corner_radius=10)
        tips_frame.grid(row=7, column=0, pady=(0, 20), sticky="ew")

        tips_text = """⌨️  GLOBAL HOTKEYS:
• Ctrl+Shift+H - Toggle overlay visibility
• Ctrl+Shift+C - Clear session and save interview log
• Ctrl+Alt+End - Emergency exit (panic button - instant kill)"""

        tips_label = ctk.CTkLabel(
            tips_frame,
            text=tips_text,
            font=("Segoe UI", 12),
            text_color=text_secondary,
            justify="left",
            anchor="w"
        )
        tips_label.pack(padx=25, pady=18, fill="x")

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

        speaker_selection = self.speaker_dropdown.get()

        if speaker_selection == "Scanning devices...":
            messagebox.showerror("Error", "Audio devices are still scanning. Please wait.")
            return

        speaker_index = None
        for device in self.speaker_devices:
            if device["name"] == speaker_selection:
                speaker_index = device["index"]
                break

        if speaker_index is None:
            messagebox.showerror("Error", "Failed to get audio device index")
            return

        # Get selected persona
        selected_persona = self.selected_persona.get()

        env_file = ".env"
        if not os.path.exists(env_file):
            with open(env_file, "w") as f:
                f.write("")

        set_key(env_file, "GROQ_API_KEY", groq_api_key)
        set_key(env_file, "SPEAKER_DEVICE_INDEX", str(speaker_index))
        set_key(env_file, "AI_PERSONA", selected_persona)

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
