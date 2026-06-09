from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from typing import Optional
import requests
from bs4 import BeautifulSoup  # pyright: ignore[reportMissingImports]
from AudioRecorder import SpeakerRecorder, MicRecorder
from AudioTranscriber import AudioTranscriber
from LLMClient import LLMClient
import asyncio
import PyPDF2
import io
import pyaudiowpatch as pyaudio


BASE_DIR = Path(__file__).resolve().parent
SESSIONS_DIR = BASE_DIR / "data" / "sessions"


class JobUrlRequest(BaseModel):
    url: str


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
        self.loop = None
        self.is_running = False
        self.is_frozen = False
        self.history_log = []
        self.history = []
        self._next_history_id = 1
        self.session_started_at = None
        self.session_ended_at = None
        self.current_llm_response = ""
        self._active_history_id = None
        self._llm_task = None

    def record_history_event(self, event: dict):
        self.history_log.append(event)

    def append_history_question(self, timestamp: str, question: str) -> dict:
        entry = {
            "id": self._next_history_id,
            "timestamp": timestamp,
            "question": question,
            "answer": "",
        }
        self._next_history_id += 1
        self.history.append(entry)
        self._active_history_id = entry["id"]
        return entry

    def update_history_answer(self, history_id: Optional[int], answer: str):
        if history_id is None:
            history_id = self._active_history_id

        if history_id is None:
            return

        for entry in self.history:
            if entry.get("id") == history_id:
                entry["answer"] = answer
                return

    def _calculate_talk_time_seconds(self) -> float:
        return sum(
            float(event.get("duration_seconds", 0) or 0)
            for event in self.history_log
            if event.get("type") == "transcript" and event.get("speaker") == "Me"
        )

    def build_session_payload(self) -> dict:
        started_at = self.session_started_at or datetime.utcnow()
        ended_at = self.session_ended_at or datetime.utcnow()
        duration_seconds = max((ended_at - started_at).total_seconds(), 0.0)
        talk_time_seconds = self._calculate_talk_time_seconds()
        talk_ratio = round((talk_time_seconds / duration_seconds) if duration_seconds else 0.0, 3)

        return {
            "session_id": started_at.strftime("session_%Y%m%d_%H%M%S"),
            "created_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
            "duration_seconds": round(duration_seconds, 2),
            "talk_time_seconds": round(talk_time_seconds, 2),
            "talk_ratio": talk_ratio,
            "persona": getattr(self.llm_client, "persona", None),
            "context": getattr(self.llm_client, "context", ""),
            "history": self.history,
            "raw_history_log": self.history_log,
        }

    def save_session(self) -> dict:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

        payload = self.build_session_payload()
        filename = f"{payload['session_id']}.json"
        payload["filename"] = filename

        session_path = SESSIONS_DIR / filename
        with session_path.open("w", encoding="utf-8") as session_file:
            json.dump(payload, session_file, indent=2, ensure_ascii=False)

        print(f"[INFO] Session saved to {session_path}")
        return payload

    def initialize(self, transcript_queue, llm_queue, loop, mic_index=None, speaker_index=None, persona="Short Bullets", context=""):
        """Initialize audio and LLM components with user configuration"""
        self.transcript_queue = transcript_queue
        self.llm_queue = llm_queue
        self.loop = loop
        self.history_log = []
        self.history = []
        self._next_history_id = 1
        self.session_started_at = datetime.utcnow()
        self.session_ended_at = None
        self.current_llm_response = ""
        self._active_history_id = None

        # Initialize audio recorders with user-selected devices
        self.speaker_recorder = SpeakerRecorder(device_index=speaker_index)
        self.mic_recorder = MicRecorder(device_index=mic_index) if mic_index is not None else None

        self.transcriber = AudioTranscriber(
            speaker_recorder=self.speaker_recorder,
            mic_recorder=self.mic_recorder,
            transcript_queue=transcript_queue,
            loop=loop
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
            self.session_ended_at = datetime.utcnow()
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

    def process_llm_for_transcript(self, transcript_text: str, history_id: Optional[int] = None):
        """Process transcript through LLM using asyncio Tasks and proper cancellation"""
        # 1. Cancel the currently running LLM task if it exists
        if self._llm_task and not self._llm_task.done():
            self._llm_task.cancel()

        async def _run_llm_async():
            try:
                async for token in self.llm_client.get_suggestion(transcript_text, request_id=history_id):
                    pass  # Tokens are pushed to the queue inside get_suggestion
            except asyncio.CancelledError:
                print("[INFO] LLM task cancelled by a newer request.")
            except Exception as e:
                print(f"[ERROR] LLM processing failed: {e}")

        # 2. Spawn the new async task
        self._llm_task = asyncio.create_task(_run_llm_async())

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

            session.record_history_event(transcript_data)

            if not session.is_frozen:
                if transcript_data.get("type") == "transcript":
                    history_entry = session.append_history_question(
                        timestamp=transcript_data.get("timestamp", datetime.utcnow().isoformat()),
                        question=transcript_data.get("text", "").strip(),
                    )
                    transcript_data["history_id"] = history_entry["id"]

                await manager.broadcast(transcript_data)

                # Trigger LLM processing for new transcript
                if transcript_data.get("type") == "transcript":
                    text = transcript_data.get("text", "")
                    if text.strip():
                        session.process_llm_for_transcript(text, history_id=transcript_data.get("history_id"))

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
                    history_id = llm_data.get("history_id")
                    current_response += token
                    session.current_llm_response = current_response

                    # Broadcast the streaming token
                    await manager.broadcast({
                        "type": "llm_hint",
                        "text": token,
                        "is_streaming": True,
                        "history_id": history_id,
                    })
                elif llm_data.get("type") == "llm_hint" and llm_data.get("clear"):
                    history_id = llm_data.get("history_id")
                    current_response = ""
                    session.current_llm_response = ""

                    await manager.broadcast({
                        "type": "llm_hint",
                        "text": "",
                        "clear": True,
                        "is_streaming": False,
                        "history_id": history_id,
                    })
                elif llm_data.get("type") == "llm_complete":
                    history_id = llm_data.get("history_id")
                    if current_response.strip():
                        session.update_history_answer(history_id, current_response.strip())
                        session.record_history_event({
                            "type": "llm_hint",
                            "speaker": "llm",
                            "text": current_response.strip(),
                            "timestamp": datetime.utcnow().isoformat(),
                            "is_streaming": False,
                            "history_id": history_id,
                        })

                    # Signal completion
                    await manager.broadcast({
                        "type": "llm_hint",
                        "text": "",
                        "is_streaming": False,
                        "complete": True,
                        "history_id": history_id,
                    })
                    current_response = ""
                    session.current_llm_response = ""

        except Exception as e:
            print(f"[ERROR] LLM worker error: {e}")
            await asyncio.sleep(0.1)


@app.on_event("startup")
async def startup_event():
    """Initialize background workers"""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

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


@app.get("/api/sessions")
def list_sessions():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    sessions = []
    for session_file in sorted(SESSIONS_DIR.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True):
        try:
            with session_file.open("r", encoding="utf-8") as file_handle:
                payload = json.load(file_handle)

            sessions.append({
                "filename": session_file.name,
                "date": payload.get("created_at") or datetime.fromtimestamp(session_file.stat().st_mtime).isoformat(),
                "duration_seconds": payload.get("duration_seconds", 0),
                "talk_ratio": payload.get("talk_ratio", 0),
            })
        except Exception as e:
            print(f"[WARNING] Failed to load session summary {session_file.name}: {e}")

    return {"success": True, "sessions": sessions}


@app.get("/api/sessions/{filename}")
def get_session(filename: str):
    safe_filename = Path(filename).name
    if safe_filename != filename or not safe_filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Invalid session filename")

    session_path = SESSIONS_DIR / safe_filename
    if not session_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    with session_path.open("r", encoding="utf-8") as file_handle:
        payload = json.load(file_handle)

    payload["filename"] = safe_filename
    return {"success": True, "session": payload}


@app.post("/api/parse_job")
def parse_job(request: JobUrlRequest):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(request.url.strip(), headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()

        extracted_text = soup.get_text(separator="\n")
        extracted_text = re.sub(r"\r", "\n", extracted_text)
        extracted_text = re.sub(r"[ \t]+", " ", extracted_text)
        extracted_text = re.sub(r"\n\s*\n+", "\n\n", extracted_text)
        extracted_text = extracted_text.strip()

        if not extracted_text:
            raise ValueError("No readable text found at the provided URL")

        return {"status": "success", "extracted_text": extracted_text}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse job URL: {e}")


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
                    loop = asyncio.get_running_loop()
                    session.initialize(
                        transcript_queue=session.transcript_queue,
                        llm_queue=session.llm_queue,
                        loop=loop,
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
                saved_session = session.save_session()
                await manager.send_json(websocket, {
                    "type": "response",
                    "action": "stop_interview",
                    "status": "stopped",
                    "message": "Interview session stopped",
                    "session": {
                        "filename": saved_session.get("filename"),
                        "date": saved_session.get("created_at"),
                        "duration_seconds": saved_session.get("duration_seconds"),
                    }
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

            elif action == "toggle_mic":
                state = data.get("state", False)
                if session.transcriber:
                    session.transcriber.set_mic_active(state)
                    # Optional: broadcast state back to all clients if needed
                    await manager.broadcast({
                        "type": "mic_status",
                        "active": state
                    })

            elif action == "change_persona":
                persona = data.get("persona")
                if persona and session.llm_client:
                    session.llm_client.set_persona(persona)
                    await manager.send_json(websocket, {
                        "type": "response",
                        "action": "change_persona",
                        "status": "success",
                        "persona": persona,
                        "message": f"Persona changed to: {persona}"
                    })
                else:
                    await manager.send_json(websocket, {
                        "type": "response",
                        "action": "change_persona",
                        "status": "error",
                        "message": "No active session or invalid persona"
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
        if session.is_running:
            session.stop()
            session.save_session()
            print("[INFO] Session auto-saved on disconnect")
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
