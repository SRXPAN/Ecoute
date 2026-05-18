import os
from groq import Groq

def get_model(use_api=None):
    return GroqWhisperTranscriber()

class GroqWhisperTranscriber:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=api_key)
        print(f"[INFO] Groq Whisper transcriber initialized")

    def get_transcription(self, wav_file_path):
        try:
            with open(wav_file_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    file=("audio.wav", audio_file.read()),
                    model="whisper-large-v3",
                    response_format="text",
                    language="en"
                )
            return transcription.strip()
        except Exception as e:
            print(f"[ERROR] Groq transcription failed: {e}")
            return ''