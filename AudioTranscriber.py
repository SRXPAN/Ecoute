import threading
import time
import os
from datetime import datetime, timedelta
from groq import Groq
from collections import deque

PHRASE_TIMEOUT = 3.0  # Seconds of silence before processing audio
MAX_PHRASES = 10  # Maximum number of phrases to keep in transcript
AUDIO_BUFFER_DURATION = 3.0  # Seconds of audio to accumulate before transcription

class AudioTranscriber:
    """
    Pure Groq API-based audio transcriber.
    No local models, no legacy speech recognition - direct API calls only.
    """

    def __init__(self, mic_recorder, speaker_recorder):
        self.mic_recorder = mic_recorder
        self.speaker_recorder = speaker_recorder

        # Initialize Groq client
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.groq_client = Groq(api_key=api_key)

        # Transcript storage
        self.transcript_data = {
            "You": deque(maxlen=MAX_PHRASES),
            "Speaker": deque(maxlen=MAX_PHRASES)
        }

        # Audio buffers
        self.audio_buffers = {
            "You": {
                "data": b"",
                "last_audio_time": None,
                "is_processing": False
            },
            "Speaker": {
                "data": b"",
                "last_audio_time": None,
                "is_processing": False
            }
        }

        self.is_running = False
        print("[INFO] Groq-based audio transcriber initialized")

    def start(self):
        """Start transcription threads"""
        if self.is_running:
            return

        self.is_running = True

        # Start audio recorders
        self.mic_recorder.start_recording()
        self.speaker_recorder.start_recording()

        # Start transcription threads
        self.mic_thread = threading.Thread(target=self._transcribe_loop, args=("You",), daemon=True)
        self.speaker_thread = threading.Thread(target=self._transcribe_loop, args=("Speaker",), daemon=True)

        self.mic_thread.start()
        self.speaker_thread.start()

        print("[INFO] Transcription started")

    def _transcribe_loop(self, source_name):
        """Main transcription loop for a specific audio source"""
        recorder = self.mic_recorder if source_name == "You" else self.speaker_recorder
        buffer_info = self.audio_buffers[source_name]

        while self.is_running:
            try:
                # Get audio chunk from recorder
                audio_chunk = recorder.get_audio_chunk(timeout=0.1)

                if audio_chunk:
                    audio_data, timestamp = audio_chunk

                    # Accumulate audio data
                    buffer_info["data"] += audio_data
                    buffer_info["last_audio_time"] = timestamp

                # Check if we should process accumulated audio
                if buffer_info["data"] and buffer_info["last_audio_time"]:
                    time_since_last_audio = (datetime.utcnow() - buffer_info["last_audio_time"]).total_seconds()

                    # Process if we have enough silence or enough audio
                    if time_since_last_audio >= PHRASE_TIMEOUT and not buffer_info["is_processing"]:
                        # Process the accumulated audio
                        self._process_audio_buffer(source_name)

                time.sleep(0.05)  # Small delay to prevent CPU spinning

            except Exception as e:
                print(f"[ERROR] Transcription loop error for {source_name}: {e}")
                time.sleep(0.5)

    def _process_audio_buffer(self, source_name):
        """Process accumulated audio buffer and send to Groq API"""
        buffer_info = self.audio_buffers[source_name]

        if not buffer_info["data"]:
            return

        # Mark as processing
        buffer_info["is_processing"] = True

        # Get audio data and clear buffer
        audio_data = buffer_info["data"]
        timestamp = buffer_info["last_audio_time"]
        buffer_info["data"] = b""

        # Process in background thread to avoid blocking
        threading.Thread(
            target=self._transcribe_with_groq,
            args=(source_name, audio_data, timestamp),
            daemon=True
        ).start()

        # Mark as not processing
        buffer_info["is_processing"] = False

    def _transcribe_with_groq(self, source_name, audio_data, timestamp):
        """Send audio to Groq API for transcription"""
        try:
            # Convert raw audio to WAV format
            recorder = self.mic_recorder if source_name == "You" else self.speaker_recorder
            wav_bytes = recorder.create_wav_bytes(audio_data)

            # Send to Groq API
            transcription = self.groq_client.audio.transcriptions.create(
                file=("audio.wav", wav_bytes),
                model="whisper-large-v3",
                response_format="text",
                language="en"  # Auto-detect or specify language
            )

            # Clean up transcription
            text = transcription.strip()

            # Filter out empty or very short transcriptions
            if text and len(text) > 3 and text.lower() not in ["you", "thank you", "thanks"]:
                # Add to transcript
                self.transcript_data[source_name].appendleft((
                    f"{source_name}: [{text}]\n\n",
                    timestamp
                ))

                print(f"[TRANSCRIPTION] {source_name}: {text}")

        except Exception as e:
            print(f"[ERROR] Groq transcription failed for {source_name}: {e}")

    def get_transcript(self):
        """Get combined transcript sorted by timestamp"""
        # Combine both transcripts
        combined = []

        for source_name in ["You", "Speaker"]:
            for text, timestamp in self.transcript_data[source_name]:
                combined.append((text, timestamp))

        # Sort by timestamp (most recent first)
        combined.sort(key=lambda x: x[1], reverse=True)

        # Return as string
        return "".join([text for text, _ in combined[:MAX_PHRASES]])

    def get_latest_speaker_text(self):
        """Get the most recent speaker (interviewer) text for AI processing"""
        if self.transcript_data["Speaker"]:
            latest_text, _ = self.transcript_data["Speaker"][0]
            # Remove formatting
            text = latest_text.replace("Speaker: [", "").replace("]\n\n", "").strip()
            return text
        return ""

    def clear_transcript_data(self):
        """Clear all transcript data"""
        self.transcript_data["You"].clear()
        self.transcript_data["Speaker"].clear()

        # Clear audio buffers
        for source_name in ["You", "Speaker"]:
            self.audio_buffers[source_name]["data"] = b""
            self.audio_buffers[source_name]["last_audio_time"] = None

        print("[INFO] Transcript data cleared")

    def stop(self):
        """Stop transcription"""
        self.is_running = False

        # Stop recorders
        self.mic_recorder.stop_recording()
        self.speaker_recorder.stop_recording()

        print("[INFO] Transcription stopped")

    def close(self):
        """Clean up resources"""
        self.stop()
        self.mic_recorder.close()
        self.speaker_recorder.close()
