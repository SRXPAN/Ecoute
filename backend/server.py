from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from typing import List, Dict
from AudioRecorder import SpeakerRecorder, MicRecorder
from AudioTranscriber import AudioTranscriber
from LLMClient import LLMClient
import threading
import PyPDF2
import io
import pyaudiowpatch as pyaudio


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"[ERROR] Failed to send message: {e}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections[:]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[ERROR] Failed to broadcast to connection: {e}")
                self.disconnect(connection)


class InterviewSession:
    def __init__(self):
        self.speaker_recorder = None
        self.mic_recorder = None
        self.transcriber = None
        self.llm_client = None
        self.transcript_queue = None
        self.llm_queue = None
        self.is_running = False
        self.is_frozen = False
        self.worker_tasks = []

    def initialize(self, transcript_queue, llm_queue, mic_index=None, speaker_index=None, persona="Short Bullets", context=""):
        """Initialize audio and LLM components with user configuration"""
        self.transcript_queue = transcript_queue
        self.llm_queue = llm_queue

        # Initialize audio recorders with user-selected devices
        self.speaker_recorder = SpeakerRecorder(device_index=speaker_index)
        self.mic_recorder = MicRecorder(device_index=mic_index) if mic_index is not None else None

        self.transcriber = AudioTranscriber(
            speaker_recorder=self.speaker_recorder,
            mic_recorder=self.mic_recorder,
            transcript_queue=transcript_queue
        )

        self.llm_client = LLMClient(
            provider="local",
            persona=persona,
            llm_queue=llm_queue
        )

        # Apply user context
        if context:
            self.llm_client.context = context
            self.llm_client.system_prompt = self.llm_client._build_system_prompt()

        print(f"[INFO] Interview session initialized (Persona: {persona}, Context: {len(context)} chars)")


    def start(self):
        """Start audio recording and transcription"""
        if not self.is_running:
            self.transcriber.start()
            self.is_running = True
            print("[INFO] Interview session started")

    def stop(self):
        """Stop audio recording and transcription"""
        if self.is_running:
            self.transcriber.stop()
            self.is_running = False
            print("[INFO] Interview session stopped")

    def freeze(self):
        """Pause transcription and LLM processing"""
        self.is_frozen = True
        if self.transcriber:
            self.transcriber.toggle_pause()
        print("[INFO] Interview session frozen")

    def unfreeze(self):
        """Resume transcription and LLM processing"""
        self.is_frozen = False
        if self.transcriber:
            self.transcriber.toggle_pause()
        print("[INFO] Interview session unfrozen")

    def process_llm_for_transcript(self, transcript_text: str):
        """Process transcript through LLM in a separate thread"""
        def _run_llm():
            try:
                for token in self.llm_client.get_suggestion(transcript_text):
                    if not self.is_frozen:
                        pass  # Tokens are already being pushed to queue
            except Exception as e:
                print(f"[ERROR] LLM processing failed: {e}")

        thread = threading.Thread(target=_run_llm, daemon=True)
        thread.start()

    def cleanup(self):
        """Clean up resources"""
        self.stop()
        if self.transcriber:
            self.transcriber.close()


app = FastAPI(title="AI Interview Assistant Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()
session = InterviewSession()


async def transcript_worker(transcript_queue: asyncio.Queue):
    """Worker that broadcasts transcript updates to all connected clients"""
    print("[INFO] Transcript worker started")
    while True:
        try:
            transcript_data = await transcript_queue.get()

            if not session.is_frozen:
                await manager.broadcast(transcript_data)

                # Trigger LLM processing for new transcript
                if transcript_data.get("type") == "transcript":
                    text = transcript_data.get("text", "")
                    if len(text) >= 10:
                        session.process_llm_for_transcript(text)

        except Exception as e:
            print(f"[ERROR] Transcript worker error: {e}")
            await asyncio.sleep(0.1)


async def llm_worker(llm_queue: asyncio.Queue):
    """Worker that broadcasts LLM tokens to all connected clients"""
    print("[INFO] LLM worker started")
    current_response = ""

    while True:
        try:
            llm_data = await llm_queue.get()

            if not session.is_frozen:
                if llm_data.get("type") == "llm_token":
                    token = llm_data.get("token", "")
                    current_response += token

                    # Broadcast the streaming token
                    await manager.broadcast({
                        "type": "llm_hint",
                        "text": token,
                        "is_streaming": True
                    })
                elif llm_data.get("type") == "llm_complete":
                    # Signal completion
                    await manager.broadcast({
                        "type": "llm_hint",
                        "text": "",
                        "is_streaming": False,
                        "complete": True
                    })
                    current_response = ""

        except Exception as e:
            print(f"[ERROR] LLM worker error: {e}")
            await asyncio.sleep(0.1)


@app.on_event("startup")
async def startup_event():
    """Initialize background workers"""
    transcript_queue = asyncio.Queue()
    llm_queue = asyncio.Queue()

    # Store queues for later initialization
    session.transcript_queue = transcript_queue
    session.llm_queue = llm_queue

    asyncio.create_task(transcript_worker(transcript_queue))
    asyncio.create_task(llm_worker(llm_queue))

    print("[INFO] Background workers initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    session.cleanup()
    print("[INFO] Server shutdown complete")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Interview Assistant Backend",
        "active_connections": len(manager.active_connections),
        "interview_running": session.is_running,
        "is_frozen": session.is_frozen
    }


@app.get("/api/audio-devices")
async def get_audio_devices():
    """
    Scan and return available audio input and output devices.

    Returns:
    - microphones: List of standard input devices
    - speakers: List of WASAPI loopback devices (for system audio capture)
    """
    try:
        p = pyaudio.PyAudio()

        microphones = []
        speakers = []

        # Scan all devices
        for i in range(p.get_device_count()):
            try:
                device_info = p.get_device_info_by_index(i)

                # Check if it's an input device (microphone)
                if device_info.get("maxInputChannels", 0) > 0:
                    # Check if it's a loopback device (speaker capture)
                    if device_info.get("isLoopbackDevice", False):
                        speakers.append({
                            "index": i,
                            "name": device_info["name"],
                            "channels": device_info["maxInputChannels"],
                            "sample_rate": int(device_info["defaultSampleRate"])
                        })
                    else:
                        microphones.append({
                            "index": i,
                            "name": device_info["name"],
                            "channels": device_info["maxInputChannels"],
                            "sample_rate": int(device_info["defaultSampleRate"])
                        })
            except Exception as e:
                print(f"[WARNING] Failed to get info for device {i}: {e}")
                continue

        p.terminate()

        return {
            "success": True,
            "microphones": microphones,
            "speakers": speakers
        }

    except Exception as e:
        print(f"[ERROR] Failed to scan audio devices: {e}")
        return {
            "success": False,
            "microphones": [],
            "speakers": [],
            "error": str(e)
        }


@app.post("/api/upload_context")
async def upload_context(file: UploadFile = File(...)):
    """
    Upload a PDF resume/context file and extract text.

    Frontend manages state - this endpoint only parses and returns extracted text.

    Returns:
    - success: boolean
    - message: status message
    - extracted_text: full extracted text from PDF
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            return {
                "success": False,
                "message": "Only PDF files are supported",
                "extracted_text": ""
            }

        # Read file contents
        contents = await file.read()

        # Extract text from PDF
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
            text_parts = []

            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    print(f"[WARNING] Failed to extract text from page {page_num}: {e}")
                    continue

            extracted_text = "\n".join(text_parts).strip()

            if not extracted_text:
                return {
                    "success": False,
                    "message": "Could not extract text from PDF. The file might be image-based or encrypted.",
                    "extracted_text": ""
                }

            return {
                "success": True,
                "message": "PDF parsed successfully",
                "extracted_text": extracted_text
            }

        except PyPDF2.errors.PdfReadError as e:
            return {
                "success": False,
                "message": f"Failed to read PDF: {str(e)}",
                "extracted_text": ""
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"PDF processing error: {str(e)}",
                "extracted_text": ""
            }

    except Exception as e:
        print(f"[ERROR] Upload context failed: {e}")
        return {
            "success": False,
            "message": f"Server error: {str(e)}",
            "extracted_text": ""
        }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        await manager.send_json(websocket, {
            "type": "connection",
            "status": "connected",
            "message": "WebSocket connection established"
        })

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "start_interview":
                # Handle both flat and nested (config) payloads
                mic_index = data.get("mic_index")
                speaker_index = data.get("speaker_index")
                persona = data.get("persona")
                context = data.get("context")

                if mic_index is None and "config" in data:
                    cfg = data.get("config", {})
                    mic_index = cfg.get("mic_index")
                    speaker_index = cfg.get("speaker_index")
                    persona = cfg.get("persona")
                    context = cfg.get("context")

                persona = persona or "Short Bullets"
                context = context or ""

                if not session.is_running:
                    # Initialize session with user configuration
                    session.initialize(
                        transcript_queue=session.transcript_queue,
                        llm_queue=session.llm_queue,
                        mic_index=mic_index,
                        speaker_index=speaker_index,
                        persona=persona,
                        context=context
                    )
                    session.start()
                    await manager.send_json(websocket, {
                        "type": "response",
                        "action": "start_interview",
                        "status": "started",
                        "message": "Interview session started"
                    })
                else:
                    await manager.send_json(websocket, {
                        "type": "response",
                        "action": "start_interview",
                        "status": "already_running",
                        "message": "Interview session already running"
                    })

            elif action == "stop_interview":
                session.stop()
                await manager.send_json(websocket, {
                    "type": "response",
                    "action": "stop_interview",
                    "status": "stopped",
                    "message": "Interview session stopped"
                })

            elif action == "freeze":
                session.freeze()
                await manager.send_json(websocket, {
                    "type": "response",
                    "action": "freeze",
                    "status": "frozen",
                    "message": "Interview session frozen"
                })

            elif action == "unfreeze":
                session.unfreeze()
                await manager.send_json(websocket, {
                    "type": "response",
                    "action": "unfreeze",
                    "status": "unfrozen",
                    "message": "Interview session unfrozen"
                })

            elif action == "ping":
                await manager.send_json(websocket, {
                    "type": "response",
                    "action": "ping",
                    "message": "pong"
                })

            else:
                await manager.send_json(websocket, {
                    "type": "response",
                    "action": action,
                    "status": "unknown",
                    "message": f"Unknown action: {action}"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("[INFO] Client disconnected")
    except Exception as e:
        print(f"[ERROR] WebSocket error: {e}")
        try:
            await manager.send_json(websocket, {
                "type": "error",
                "message": str(e)
            })
        except:
            pass
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
