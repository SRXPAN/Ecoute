import threading
import time
import os
from datetime import datetime
import numpy as np
from groq import Groq
from collections import deque

PHRASE_TIMEOUT = 1.0
MAX_PHRASES = 10
MAX_PHRASE_DURATION = 8.0
RMS_THRESHOLD = 30  # ЗНИЖЕНО: Тепер краще ловить звичайну мову

class AudioTranscriber:
    def __init__(self, speaker_recorder):
        self.speaker_recorder = speaker_recorder

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.groq_client = Groq(api_key=api_key)

        self.transcript_data = {
            "Speaker": deque(maxlen=MAX_PHRASES)
        }

        self.audio_buffers = {
            "Speaker": {"data": b"", "last_audio_time": None, "start_time": None, "is_processing": False}
        }

        # СТАТУСИ ДЛЯ ІНТЕРФЕЙСУ
        self.current_status = {"Speaker": "🟢 Idle"}

        self.is_running = False
        self.is_paused = False  # Manual pause toggle
        print("[INFO] Groq-based audio transcriber initialized with Smart VAD (Speaker only)")

    def start(self):
        if self.is_running: return
        self.is_running = True
        self.speaker_recorder.start_recording()

        self.speaker_thread = threading.Thread(target=self._transcribe_loop, args=("Speaker",), daemon=True)

        self.speaker_thread.start()
        print("[INFO] Transcription started (Speaker only)")

    def _transcribe_loop(self, source_name):
        recorder = self.speaker_recorder
        buffer_info = self.audio_buffers[source_name]

        while self.is_running:
            try:
                # If paused, aggressively clear buffers and skip processing
                if self.is_paused:
                    audio_chunk = recorder.get_audio_chunk(timeout=0.1)
                    # Throw away audio data while paused
                    if audio_chunk:
                        pass  # Discard the chunk

                    # Clear any accumulated buffer
                    if buffer_info["data"]:
                        buffer_info["data"] = b""
                        buffer_info["last_audio_time"] = None
                        buffer_info["start_time"] = None

                    time.sleep(0.1)
                    continue

                audio_chunk = recorder.get_audio_chunk(timeout=0.1)

                if audio_chunk:
                    audio_data, timestamp = audio_chunk

                    audio_np = np.frombuffer(audio_data, dtype=np.int16)
                    rms = np.sqrt(np.mean(audio_np.astype(np.float32)**2))

                    if rms > RMS_THRESHOLD:
                        self.current_status[source_name] = "🎙️ Recording"
                        if not buffer_info["data"]:
                            buffer_info["start_time"] = timestamp

                        buffer_info["data"] += audio_data
                        buffer_info["last_audio_time"] = timestamp
                    else:
                        if not buffer_info["is_processing"] and not buffer_info["data"]:
                            self.current_status[source_name] = "🟢 Idle"
                        elif buffer_info["data"] and not buffer_info["is_processing"]:
                            self.current_status[source_name] = "🟡 Buffering"

                if buffer_info["data"] and buffer_info["last_audio_time"]:
                    time_since_last_audio = (datetime.utcnow() - buffer_info["last_audio_time"]).total_seconds()

                    start_t = buffer_info["start_time"] if buffer_info["start_time"] else buffer_info["last_audio_time"]
                    duration = (datetime.utcnow() - start_t).total_seconds()

                    if (time_since_last_audio >= PHRASE_TIMEOUT or duration >= MAX_PHRASE_DURATION) and not buffer_info["is_processing"]:
                        self._process_audio_buffer(source_name)

                time.sleep(0.02)

            except Exception as e:
                print(f"[ERROR] Transcription loop error for {source_name}: {e}")
                self.current_status[source_name] = "🔴 Error"
                time.sleep(0.5)

    def _process_audio_buffer(self, source_name):
        buffer_info = self.audio_buffers[source_name]
        if not buffer_info["data"]: return

        buffer_info["is_processing"] = True
        self.current_status[source_name] = "🟠 Processing"

        audio_data = buffer_info["data"]
        timestamp = buffer_info["last_audio_time"]

        buffer_info["data"] = b""
        buffer_info["start_time"] = None

        threading.Thread(
            target=self._transcribe_with_groq,
            args=(source_name, audio_data, timestamp),
            daemon=True
        ).start()

        buffer_info["is_processing"] = False

    def _transcribe_with_groq(self, source_name, audio_data, timestamp):
        try:
            self.current_status[source_name] = "⏳ Groq API"

            recorder = self.speaker_recorder
            wav_bytes = recorder.create_wav_bytes(audio_data)

            transcription = self.groq_client.audio.transcriptions.create(
                file=("audio.wav", wav_bytes),
                model="whisper-large-v3",
                response_format="text",
            )

            text = transcription.strip()
            hallucinations = ["you", "thank you", "thanks", "you.", "thanks.", "thank you.", "subtitles by"]
            if text and len(text) > 3 and not any(h in text.lower() for h in hallucinations):
                self.transcript_data[source_name].appendleft((f"{source_name}: [{text}]\n\n", timestamp))
                print(f"[TRANSCRIPTION] {source_name}: {text}")

            self.current_status[source_name] = "🟢 Idle"

        except Exception as e:
            print(f"[ERROR] Groq transcription failed for {source_name}: {e}")
            self.current_status[source_name] = "🔴 Error"
            time.sleep(2)  # Чекаємо 2 сек перед поверненням до Idle
            self.current_status[source_name] = "🟢 Idle"

    def get_transcript(self):
        combined = []
        for text, timestamp in self.transcript_data["Speaker"]:
            combined.append((text, timestamp))
        combined.sort(key=lambda x: x[1], reverse=True)
        return "".join([text for text, _ in combined[:MAX_PHRASES]])

    def get_latest_speaker_text(self):
        if self.transcript_data["Speaker"]:
            latest_text, _ = self.transcript_data["Speaker"][0]
            return latest_text.replace("Speaker: [", "").replace("]\n\n", "").strip()
        return ""

    def get_statuses(self):
        if self.is_paused:
            return "⏸️ PAUSED"
        return self.current_status['Speaker']

    def toggle_pause(self) -> bool:
        """Toggle pause state and return new state"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            print("[INFO] Transcription PAUSED - audio buffers will be cleared")
        else:
            print("[INFO] Transcription RESUMED")
        return self.is_paused

    def clear_transcript_data(self):
        self.transcript_data["Speaker"].clear()
        self.audio_buffers["Speaker"]["data"] = b""
        self.audio_buffers["Speaker"]["last_audio_time"] = None
        self.audio_buffers["Speaker"]["start_time"] = None
        print("[INFO] Transcript data cleared")

    def stop(self):
        self.is_running = False
        self.speaker_recorder.stop_recording()
        print("[INFO] Transcription stopped")

    def close(self):
        self.stop()
        self.speaker_recorder.close()

