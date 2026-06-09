import threading
import time
import os
from datetime import datetime
import numpy as np
import keyboard
from groq import Groq
from collections import deque
import asyncio
import webrtcvad

PHRASE_TIMEOUT = 2.8
MAX_PHRASES = 10
MAX_PHRASE_DURATION = 8.0
MIC_SILENCE_THRESHOLD = 500

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

        # WebRTC VAD initialization (aggressiveness level 3 = most aggressive)
        self.vad = webrtcvad.Vad(3)

        # VAD frame buffers (30ms chunks per source)
        self.vad_buffers = {
            "Interviewer": b"",
            "Me": b""
        }

        self.current_status = {
            "Interviewer": "🟢 Idle",
            "Me": "🟢 Idle"
        }

        self.is_running = False
        self.is_paused = False
        print(f"[INFO] Groq-based audio transcriber initialized with WebRTC VAD (Speaker + {'Mic' if mic_recorder else 'No Mic'})")

    def _is_push_to_talk_active(self) -> bool:
        """Require Ctrl + Alt to be held before we process microphone audio."""
        try:
            return keyboard.is_pressed("ctrl") and keyboard.is_pressed("alt")
        except Exception:
            # If the keyboard hook is unavailable, fail closed so we do not
            # transcribe background noise or accidental keystrokes.
            return False

    def _is_speech_detected(self, audio_data: bytes, sample_rate: int, source_name: str) -> bool:
        """
        Use WebRTC VAD to detect speech in audio chunks.
        VAD requires exact frame sizes: 10ms, 20ms, or 30ms at 8000, 16000, 32000, or 48000 Hz.
        We buffer incoming audio and process it in 30ms frames.
        """
        if not audio_data:
            return False

        # Add incoming audio to the VAD buffer
        self.vad_buffers[source_name] += audio_data

        # Calculate frame size for 30ms at the given sample rate
        # Frame size = (sample_rate * 30ms) * 2 bytes per sample (int16)
        frame_duration_ms = 30
        frame_size = int((sample_rate / 1000) * frame_duration_ms * 2)

        speech_detected = False

        # Process complete 30ms frames
        while len(self.vad_buffers[source_name]) >= frame_size:
            frame = self.vad_buffers[source_name][:frame_size]
            self.vad_buffers[source_name] = self.vad_buffers[source_name][frame_size:]

            try:
                if self.vad.is_speech(frame, sample_rate):
                    speech_detected = True
            except Exception as e:
                print(f"[WARNING] VAD processing failed for {source_name}: {e}")
                # Fallback: assume speech if we can't process
                speech_detected = True
                break

        return speech_detected

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

                    # Push-to-talk only applies to the microphone. If the user is
                    # not holding Ctrl + Alt, discard the audio immediately.
                    if source_name == "Me" and not self._is_push_to_talk_active():
                        if buffer_info["data"]:
                            buffer_info["data"] = b""
                            buffer_info["last_audio_time"] = None
                            buffer_info["start_time"] = None
                        self.vad_buffers[source_name] = b""
                        self.current_status[source_name] = "🟢 Idle"
                        time.sleep(0.02)
                        continue

                    # Get sample rate from recorder
                    sample_rate = int(recorder.device_info["defaultSampleRate"])

                    # Use WebRTC VAD for speech detection
                    is_speech = self._is_speech_detected(audio_data, sample_rate, source_name)

                    # For microphone input, also check RMS to filter out very quiet audio
                    if source_name == "Me":
                        audio_np = np.frombuffer(audio_data, dtype=np.int16) if audio_data else np.array([], dtype=np.int16)
                        rms = float(np.sqrt(np.mean(audio_np.astype(np.float32) ** 2))) if audio_np.size > 0 else 0.0

                        if rms < MIC_SILENCE_THRESHOLD:
                            if not buffer_info["is_processing"] and not buffer_info["data"]:
                                self.current_status[source_name] = "🟢 Idle"
                            continue

                    if is_speech:
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
        start_time = buffer_info["start_time"] or timestamp
        buffer_duration = max((timestamp - start_time).total_seconds(), 0.01) if timestamp and start_time else 0.01

        # Guard the Groq request with a final RMS check for microphone audio.
        # This is the last cheap filter before transcription.
        if source_name == "Me":
            audio_np = np.frombuffer(audio_data, dtype=np.int16) if audio_data else np.array([], dtype=np.int16)
            rms = float(np.sqrt(np.mean(audio_np.astype(np.float32) ** 2))) if audio_np.size > 0 else 0.0

            if rms < MIC_SILENCE_THRESHOLD:
                buffer_info["data"] = b""
                buffer_info["start_time"] = None
                buffer_info["last_audio_time"] = None
                buffer_info["is_processing"] = False
                self.current_status[source_name] = "🟢 Idle"
                return

        buffer_info["data"] = b""
        buffer_info["start_time"] = None

        threading.Thread(
            target=self._transcribe_with_groq,
            args=(source_name, audio_data, timestamp, buffer_duration, recorder),
            daemon=True
        ).start()

        buffer_info["is_processing"] = False

    def _transcribe_with_groq(self, source_name, audio_data, timestamp, buffer_duration, recorder):
        try:
            self.current_status[source_name] = "⏳ Groq API"
            wav_bytes = recorder.create_wav_bytes(audio_data)

            transcription = self.groq_client.audio.transcriptions.create(
                file=("audio.wav", wav_bytes),
                model="whisper-large-v3",
                response_format="text",
            )

            text = transcription.strip()
            word_count = len(text.split()) if text else 0
            minutes_spoken = max(buffer_duration / 60.0, 1 / 60.0)
            wpm = round(word_count / minutes_spoken, 1) if word_count else 0.0
            is_speaking_too_fast = source_name == "Me" and wpm > 160
            hallucinations = [
                "you", "thank you", "thanks", "you.", "thanks.", "thank you.", "subtitles by",
                "субтитры сделал dimatorzok", "субтитры сделал", "dimatorzok", "перевод и озвучка",
                "or movie virushili", "movie virushili", "pireti zed"
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
                                "timestamp": timestamp.isoformat(),
                                "duration_seconds": round(buffer_duration, 2),
                                "word_count": word_count,
                                "wpm": wpm,
                                "is_speaking_too_fast": is_speaking_too_fast,
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
            self.vad_buffers[source] = b""
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
