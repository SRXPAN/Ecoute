import pyaudiowpatch as pyaudio
import wave
import io
import threading
from datetime import datetime
from queue import Queue

CHUNK_SIZE = 1024
RECORD_SECONDS = 3
SAMPLE_WIDTH = 2  # 16-bit audio

class AudioRecorder:
    """
    Pure PyAudio-based audio recorder for microphone and speaker capture.
    No legacy speech recognition wrappers - direct audio buffer management.
    """

    def __init__(self, device_index=None, is_speaker=False):
        self.device_index = device_index
        self.is_speaker = is_speaker
        self.audio_queue = Queue()
        self.is_recording = False
        self.stream = None
        self.p = pyaudio.PyAudio()

        # Get device info
        if is_speaker:
            self.device_info = self._get_speaker_device()
        else:
            self.device_info = self._get_mic_device()

        print(f"[INFO] Initialized {'Speaker' if is_speaker else 'Mic'} recorder: {self.device_info['name']}")

    def _get_mic_device(self):
        """Get microphone device info"""
        if self.device_index is not None:
            return self.p.get_device_info_by_index(self.device_index)
        else:
            # Use default input device
            wasapi_info = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
            return self.p.get_device_info_by_index(wasapi_info["defaultInputDevice"])

    def _get_speaker_device(self):
        """Get speaker loopback device info"""
        if self.device_index is not None:
            device = self.p.get_device_info_by_index(self.device_index)
            # If it's already a loopback device, use it
            if device.get("isLoopbackDevice", False):
                return device
            # Otherwise, find the corresponding loopback device
            for loopback in self.p.get_loopback_device_info_generator():
                if device["name"] in loopback["name"]:
                    return loopback
        else:
            # Use default output device's loopback
            wasapi_info = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = self.p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

            for loopback in self.p.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    return loopback

        raise ValueError("Could not find loopback device for speaker capture")

    def start_recording(self):
        """Start recording audio in a background thread"""
        if self.is_recording:
            return

        self.is_recording = True

        # Use device's native sample rate and channels to avoid -9997 error
        sample_rate = int(self.device_info["defaultSampleRate"])
        channels = int(self.device_info["maxInputChannels"]) if self.is_speaker else 1

        # Open audio stream
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=self.device_info["index"],
            frames_per_buffer=CHUNK_SIZE,
            stream_callback=self._audio_callback
        )

        self.stream.start_stream()
        print(f"[INFO] Started recording from {'speaker' if self.is_speaker else 'microphone'} at {sample_rate}Hz")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio stream"""
        if self.is_recording:
            timestamp = datetime.utcnow()
            self.audio_queue.put((in_data, timestamp))
        return (None, pyaudio.paContinue)

    def get_audio_chunk(self, timeout=0.1):
        """Get audio chunk from queue (non-blocking)"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except:
            return None

    def create_wav_bytes(self, audio_data):
        """Convert raw audio data to WAV format bytes"""
        wav_buffer = io.BytesIO()

        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(int(self.device_info["maxInputChannels"]) if self.is_speaker else 1)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(int(self.device_info["defaultSampleRate"]))
            wf.writeframes(audio_data)

        wav_buffer.seek(0)
        return wav_buffer.read()

    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        print(f"[INFO] Stopped recording from {'speaker' if self.is_speaker else 'microphone'}")

    def close(self):
        """Clean up resources"""
        self.stop_recording()
        self.p.terminate()


class MicRecorder(AudioRecorder):
    """Microphone audio recorder"""

    def __init__(self, device_index=None):
        super().__init__(device_index=device_index, is_speaker=False)


class SpeakerRecorder(AudioRecorder):
    """Speaker loopback audio recorder"""

    def __init__(self, device_index=None):
        super().__init__(device_index=device_index, is_speaker=True)


# For backward compatibility with main.py
class DefaultMicRecorder(MicRecorder):
    pass


class DefaultSpeakerRecorder(SpeakerRecorder):
    pass
