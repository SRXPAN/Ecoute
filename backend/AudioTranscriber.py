import threading
import time
import os
from datetime import datetime
import numpy as np
from groq import Groq
from collections import deque
import asyncio

PHRASE_TIMEOUT = 1.0
MAX_PHRASES = 10
MAX_PHRASE_DURATION = 8.0
RMS_THRESHOLD = 30

class AudioTranscriber:
    def __init__(self, speaker_recorder, mic_recorder=None, transcript_queue=None, loop=None):
        self.speaker_recorder = speaker_recorder
        self.mic_recorder = mic_recorder
        self.transcript_queue = transcript_queue  # asyncio.Queue for output
        self.loop = loop

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.groq_client = Groq(api_key=api_key)

        self.transcript_data = {
            "Interviewer": deque(maxlen=MAX_PHRASES),
            "Me": deque(maxlen=MAX_PHRASES)
        }

        self.audio_buffers = {
            "Interviewer": {"data": b"", "last_audio_time": None, "start_time": None, "is_processing": False},
            "Me": {"data": b"", "last_audio_time": None, "start_time": None, "is_processing": False}
        }

        self.current_status = {
            "Interviewer": "🟢 Idle",
            "Me": "🟢 Idle"
        }

        self.is_running = False
        self.is_paused = False
        print(f"[INFO] Groq-based audio transcriber initialized (Speaker + {'Mic' if mic_recorder else 'No Mic'})")

    def start(self):
        if self.is_running: return
        self.is_running = True
        
        # Start recorders
        self.speaker_recorder.start_recording()
        if self.mic_recorder:
            self.mic_recorder.start_recording()

        # Start transcription threads
        self.speaker_thread = threading.Thread(target=self._transcribe_loop, args=("Interviewer", self.speaker_recorder), daemon=True)
        self.speaker_thread.start()
        
        if self.mic_recorder:
            self.mic_thread = threading.Thread(target=self._transcribe_loop, args=("Me", self.mic_recorder), daemon=True)
            self.mic_thread.start()
            
        print(f"[INFO] Transcription started for: Interviewer{' & Me' if self.mic_recorder else ''}")

    def _transcribe_loop(self, source_name, recorder):
        buffer_info = self.audio_buffers[source_name]

        while self.is_running:
            try:
                # If paused, aggressively clear buffers and skip processing
                if self.is_paused:
                    audio_chunk = recorder.get_audio_chunk(timeout=0.1)
                    if audio_chunk:
                        pass  # Discard
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
                        self._process_audio_buffer(source_name, recorder)

                time.sleep(0.02)

            except Exception as e:
                print(f"[ERROR] Transcription loop error for {source_name}: {e}")
                self.current_status[source_name] = "🔴 Error"
                time.sleep(0.5)

    def _process_audio_buffer(self, source_name, recorder):
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
            args=(source_name, audio_data, timestamp, recorder),
            daemon=True
        ).start()

        buffer_info["is_processing"] = False

    def _transcribe_with_groq(self, source_name, audio_data, timestamp, recorder):
        try:
            self.current_status[source_name] = "⏳ Groq API"
            wav_bytes = recorder.create_wav_bytes(audio_data)

            transcription = self.groq_client.audio.transcriptions.create(
                file=("audio.wav", wav_bytes),
                model="whisper-large-v3",
                response_format="text",
            )

            text = transcription.strip()
            hallucinations = [
                "you", "thank you", "thanks", "you.", "thanks.", "thank you.", "subtitles by",
                "субтитры сделал dimatorzok", "субтитры сделал", "dimatorzok", "перевод и озвучка"
            ]
            if text and len(text) > 3 and not any(h in text.lower() for h in hallucinations):
                self.transcript_data[source_name].appendleft((f"{source_name}: [{text}]\n\n", timestamp))
                print(f"[TRANSCRIPTION] {source_name}: {text}")

                if self.transcript_queue and self.loop:
                    try:
                        self.loop.call_soon_threadsafe(
                            self.transcript_queue.put_nowait,
                            {
                                "type": "transcript",
                                "speaker": source_name,
                                "text": text,
                                "timestamp": timestamp.isoformat()
                            }
                        )
                    except Exception as e:
                        print(f"[WARNING] Failed to push transcript to queue: {e}")

            self.current_status[source_name] = "🟢 Idle"

        except Exception as e:
            print(f"[ERROR] Groq transcription failed for {source_name}: {e}")
            self.current_status[source_name] = "🔴 Error"
            time.sleep(2)
            self.current_status[source_name] = "🟢 Idle"

    def get_transcript(self):
        combined = []
        for source in ["Interviewer", "Me"]:
            for text, timestamp in self.transcript_data[source]:
                combined.append((text, timestamp))
        combined.sort(key=lambda x: x[1], reverse=True)
        return "".join([text for text, _ in combined[:MAX_PHRASES]])

    def get_latest_speaker_text(self):
        # We prefer Interviewer text for LLM hints usually, but let's just return the absolute latest
        all_text = []
        for source in ["Interviewer", "Me"]:
            if self.transcript_data[source]:
                text, timestamp = self.transcript_data[source][0]
                all_text.append((text, timestamp))
        
        if not all_text:
            return ""
            
        all_text.sort(key=lambda x: x[1], reverse=True)
        latest_text, _ = all_text[0]
        # Clean up tags
        return latest_text.split(": [")[-1].replace("]\n\n", "").strip()

    def get_statuses(self):
        if self.is_paused:
            return "⏸️ PAUSED"
        return f"Int: {self.current_status['Interviewer']} | Me: {self.current_status['Me']}"

    def toggle_pause(self) -> bool:
        """Toggle pause state and return new state"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            print("[INFO] Transcription PAUSED - audio buffers will be cleared")
        else:
            print("[INFO] Transcription RESUMED")
        return self.is_paused

    def clear_transcript_data(self):
        for source in ["Interviewer", "Me"]:
            self.transcript_data[source].clear()
            self.audio_buffers[source]["data"] = b""
            self.audio_buffers[source]["last_audio_time"] = None
            self.audio_buffers[source]["start_time"] = None
        print("[INFO] Transcript data cleared")

    def stop(self):
        self.is_running = False
        self.speaker_recorder.stop_recording()
        if self.mic_recorder:
            self.mic_recorder.stop_recording()
        print("[INFO] Transcription stopped")

    def close(self):
        self.stop()
        self.speaker_recorder.close()
        if self.mic_recorder:
            self.mic_recorder.close()
