from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from typing import List
from AudioRecorder import SpeakerRecorder
from AudioTranscriber import AudioTranscriber
from LLMClient import LLMClient
import threading
import PyPDF2
import io


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
        self.transcriber = None
        self.llm_client = None
        self.transcript_queue = None
        self.llm_queue = None
        self.is_running = False
        self.is_frozen = False
        self.worker_tasks = []
        self.current_context = ""  # Store uploaded context

    def initialize(self, transcript_queue, llm_queue):
        """Initialize audio and LLM components"""
        self.transcript_queue = transcript_queue
        self.llm_queue = llm_queue

        self.speaker_recorder = SpeakerRecorder()
        self.transcriber = AudioTranscriber(
            speaker_recorder=self.speaker_recorder,
            transcript_queue=transcript_queue
        )
        self.llm_client = LLMClient(
            provider="local",
            persona="Short Bullets",
            llm_queue=llm_queue
        )

        # Apply current context if available
        if self.current_context:
            self.llm_client.context = self.current_context
            self.llm_client.system_prompt = self.llm_client._build_system_prompt()

        print("[INFO] Interview session initialized")

    def update_context(self, context: str):
        """Update the context for LLM client"""
        self.current_context = context
        if self.llm_client:
            self.llm_client.context = context
            self.llm_client.system_prompt = self.llm_client._build_system_prompt()
            print(f"[INFO] Context updated ({len(context)} characters)")

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

    session.initialize(transcript_queue, llm_queue)

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


@app.post("/api/upload_context")
async def upload_context(file: UploadFile = File(...)):
    """
    Upload a PDF resume/context file and extract text for LLM context.

    Handles:
    - PDF text extraction using PyPDF2
    - Graceful error handling for unreadable PDFs
    - Updates global session context for LLM

    Returns:
    - success: boolean
    - message: status message
    - context_length: character count of extracted text
    - preview: first 200 characters of extracted text
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            return {
                "success": False,
                "message": "Only PDF files are supported",
                "context_length": 0,
                "preview": ""
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
                    "context_length": 0,
                    "preview": ""
                }

            # Update session context
            session.update_context(extracted_text)

            preview = extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text

            return {
                "success": True,
                "message": "Context uploaded successfully",
                "context_length": len(extracted_text),
                "preview": preview
            }

        except PyPDF2.errors.PdfReadError as e:
            return {
                "success": False,
                "message": f"Failed to read PDF: {str(e)}",
                "context_length": 0,
                "preview": ""
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"PDF processing error: {str(e)}",
                "context_length": 0,
                "preview": ""
            }

    except Exception as e:
        print(f"[ERROR] Upload context failed: {e}")
        return {
            "success": False,
            "message": f"Server error: {str(e)}",
            "context_length": 0,
            "preview": ""
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
                if not session.is_running:
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
