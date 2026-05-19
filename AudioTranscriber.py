import threading
import time
import os
from datetime import datetime
import numpy as np
from groq import Groq
from collections import deque

PHRASE_TIMEOUT = 1.0  # Секунд тиші для відправки тексту
MAX_PHRASES = 10
MAX_PHRASE_DURATION = 8.0
RMS_THRESHOLD = 150  # Поріг гучності. Звуки тихіші за це значення вважатимуться абсолютною тишею.

class AudioTranscriber:
    def __init__(self, mic_recorder, speaker_recorder):
        self.mic_recorder = mic_recorder
        self.speaker_recorder = speaker_recorder

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.groq_client = Groq(api_key=api_key)

        self.transcript_data = {
            "You": deque(maxlen=MAX_PHRASES),
            "Speaker": deque(maxlen=MAX_PHRASES)
        }

        self.audio_buffers = {
            "You": {"data": b"", "last_audio_time": None, "start_time": None, "is_processing": False},
            "Speaker": {"data": b"", "last_audio_time": None, "start_time": None, "is_processing": False}
        }

        self.is_running = False
        print("[INFO] Groq-based audio transcriber initialized with Smart VAD")

    def start(self):
        if self.is_running: return
        self.is_running = True
        self.mic_recorder.start_recording()
        self.speaker_recorder.start_recording()

        self.mic_thread = threading.Thread(target=self._transcribe_loop, args=("You",), daemon=True)
        self.speaker_thread = threading.Thread(target=self._transcribe_loop, args=("Speaker",), daemon=True)

        self.mic_thread.start()
        self.speaker_thread.start()
        print("[INFO] Transcription started")

    def _transcribe_loop(self, source_name):
        recorder = self.mic_recorder if source_name == "You" else self.speaker_recorder
        buffer_info = self.audio_buffers[source_name]

        while self.is_running:
            try:
                audio_chunk = recorder.get_audio_chunk(timeout=0.1)

                if audio_chunk:
                    audio_data, timestamp = audio_chunk

                    # Розумний VAD (Аналіз гучності)
                    audio_np = np.frombuffer(audio_data, dtype=np.int16)
                    # Рахуємо гучність шматка
                    rms = np.sqrt(np.mean(audio_np.astype(np.float32)**2))

                    # Додаємо аудіо в буфер ТІЛЬКИ якщо воно гучніше за фоновий шум
                    if rms > RMS_THRESHOLD:
                        if not buffer_info["data"]:
                            buffer_info["start_time"] = timestamp

                        buffer_info["data"] += audio_data
                        buffer_info["last_audio_time"] = timestamp

                # Якщо в буфері є накопичений голос, перевіряємо, чи пора відправляти
                if buffer_info["data"] and buffer_info["last_audio_time"]:
                    # Оскільки тихі звуки ігноруються, time_since_last_audio буде реально зростати під час тиші!
                    time_since_last_audio = (datetime.utcnow() - buffer_info["last_audio_time"]).total_seconds()

                    start_t = buffer_info["start_time"] if buffer_info["start_time"] else buffer_info["last_audio_time"]
                    duration = (datetime.utcnow() - start_t).total_seconds()

                    # Відправляємо якщо настала реальна тиша (1 сек) АБО людина моноложить 8 сек
                    if (time_since_last_audio >= PHRASE_TIMEOUT or duration >= MAX_PHRASE_DURATION) and not buffer_info["is_processing"]:
                        self._process_audio_buffer(source_name)

                time.sleep(0.02)

            except Exception as e:
                print(f"[ERROR] Transcription loop error for {source_name}: {e}")
                time.sleep(0.5)

    def _process_audio_buffer(self, source_name):
        buffer_info = self.audio_buffers[source_name]
        if not buffer_info["data"]: return

        buffer_info["is_processing"] = True
        audio_data = buffer_info["data"]
        timestamp = buffer_info["last_audio_time"]

        # Очищаємо буфер миттєво, щоб ловити наступні слова
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
            recorder = self.mic_recorder if source_name == "You" else self.speaker_recorder
            wav_bytes = recorder.create_wav_bytes(audio_data)

            transcription = self.groq_client.audio.transcriptions.create(
                file=("audio.wav", wav_bytes),
                model="whisper-large-v3",
                response_format="text",
            )

            text = transcription.strip()
            # Фільтруємо типові галюцинації Whisper, які виникають на шумах
            hallucinations = ["you", "thank you", "thanks", "you.", "thanks.", "thank you.", "subtitles by"]
            if text and len(text) > 3 and not any(h in text.lower() for h in hallucinations):
                self.transcript_data[source_name].appendleft((f"{source_name}: [{text}]\n\n", timestamp))
                print(f"[TRANSCRIPTION] {source_name}: {text}")

        except Exception as e:
            print(f"[ERROR] Groq transcription failed for {source_name}: {e}")

    def get_transcript(self):
        combined = []
        for source_name in ["You", "Speaker"]:
            for text, timestamp in self.transcript_data[source_name]:
                combined.append((text, timestamp))
        combined.sort(key=lambda x: x[1], reverse=True)
        return "".join([text for text, _ in combined[:MAX_PHRASES]])

    def get_latest_speaker_text(self):
        if self.transcript_data["Speaker"]:
            latest_text, _ = self.transcript_data["Speaker"][0]
            return latest_text.replace("Speaker: [", "").replace("]\n\n", "").strip()
        return ""

    def clear_transcript_data(self):
        self.transcript_data["You"].clear()
        self.transcript_data["Speaker"].clear()
        for source_name in ["You", "Speaker"]:
            self.audio_buffers[source_name]["data"] = b""
            self.audio_buffers[source_name]["last_audio_time"] = None
            self.audio_buffers[source_name]["start_time"] = None
        print("[INFO] Transcript data cleared")

    def stop(self):
        self.is_running = False
        self.mic_recorder.stop_recording()
        self.speaker_recorder.stop_recording()
        print("[INFO] Transcription stopped")

    def close(self):
        self.stop()
        self.mic_recorder.close()
        self.speaker_recorder.close()
