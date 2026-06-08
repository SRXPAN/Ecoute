import os
from typing import Generator
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LLMClient:
    """
    LLM client manager utilizing local LM Studio server via OpenAI-compatible API.
    Optimized for real-time streaming and safe memory management.
    GUI-independent version with queue support.
    """

    def __init__(self, provider: str = "local", persona: str = "Short Bullets", llm_queue=None, loop=None):
        self.provider = provider.lower()
        self.persona = persona
        self.llm_queue = llm_queue  # asyncio.Queue for streaming output
        self.loop = loop
        self.model_name = 'local-model'
        self.context = self._load_interview_context()
        self.system_prompt = self._build_system_prompt()
        self.history = []
        self.max_history_messages = 10

        self.client = OpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio"
        )

        print(f"[INFO] Local LLM client initialized successfully (Persona: {self.persona}), connecting to LM Studio at http://127.0.0.1:1234")

    def _load_interview_context(self) -> str:
        context_file = "temp_context.txt"
        if os.path.exists(context_file):
            try:
                with open(context_file, "r", encoding="utf-8") as f:
                    context = f.read().strip()
                    if context:
                        print(f"[INFO] Loaded interview context ({len(context)} characters)")
                        return context
            except Exception as e:
                print(f"[WARNING] Failed to load context file: {e}")
        return ""

    def _build_system_prompt(self) -> str:
        """
        Dynamically builds the system prompt based on the selected AI persona.
        """
        if self.persona == "Interview Copilot":
            base_prompt = (
                "You are an expert IT professional assisting the user with a technical interview. "
                "The user's background is provided in the Context. Listen to the interviewer's questions "
                "and provide complete, comprehensive, and highly detailed answers to help the user pass the interview. "
                "Do not restrict your format; use your extensive knowledge to give the best possible full answer. "
                "Answer in the language the interviewer is speaking (usually Ukrainian or Russian)."
            )
        elif self.persona == "Client English Assistant":
            base_prompt = (
                "You are a real-time English translator and Project Management assistant. The user is on a call "
                "with an English-speaking client, but the user does not speak English well. The current project tasks "
                "and context are provided below. When the client speaks, briefly summarize what they want in Ukrainian or Russian. "
                "Then, provide the EXACT professional English phrases the user should read out loud to reply, manage the task, or guide the conversation. "
                "Format: [Суть питання] -> [Your English Reply]."
            )
        else:
            base_prompt = (
                "You are a Professional Copilot assistant. Use the user's context to help them respond clearly, "
                "professionally, and naturally in the language of the conversation."
            )

        context_str = self.context if self.context else "[No context provided]"
        return f"{base_prompt}\n\nCONTEXT (User's Background):\n{context_str}"

    def _trim_history(self):
        """Keep only the most recent conversation messages to prevent token overflow."""
        if len(self.history) > self.max_history_messages:
            self.history = self.history[-self.max_history_messages:]

    def _build_messages(self, interviewer_question: str):
        """Always include the system prompt and only the last 10 history messages."""
        recent_history = self.history[-self.max_history_messages:]
        return [
            {'role': 'system', 'content': self.system_prompt}
        ] + recent_history + [
            {'role': 'user', 'content': interviewer_question}
        ]

    def get_suggestion(self, interviewer_question: str) -> Generator[str, None, None]:
        """Stream AI suggestions token by token"""
        if not interviewer_question or len(interviewer_question.strip()) < 10:
            return

        try:
            clear_sent = False
            messages = self._build_messages(interviewer_question)

            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content

                    if not clear_sent and self.llm_queue and self.loop:
                        try:
                            self.loop.call_soon_threadsafe(
                                self.llm_queue.put_nowait,
                                {
                                    "type": "llm_hint",
                                    "text": "",
                                    "clear": True
                                }
                            )
                            clear_sent = True
                        except Exception as e:
                            print(f"[WARNING] Failed to push LLM clear signal to queue: {e}")

                    full_response += token

                    # Push to async queue if available
                    if self.llm_queue and self.loop:
                        try:
                            self.loop.call_soon_threadsafe(
                                self.llm_queue.put_nowait,
                                {
                                    "type": "llm_token",
                                    "token": token
                                }
                            )
                        except Exception as e:
                            print(f"[WARNING] Failed to push LLM token to queue: {e}")

                    yield token

            # Save to conversation history
            self.history.append({'role': 'user', 'content': interviewer_question})
            self.history.append({'role': 'assistant', 'content': full_response})
            self._trim_history()

        except Exception as e:
            print(f"[ERROR] Local LM Studio streaming failed: {e}")
            print(f"[ERROR] Make sure LM Studio server is running at http://127.0.0.1:1234")
            yield ""

    def get_suggestion_sync(self, interviewer_question: str) -> str:
        """Non-streaming fallback method (for testing or error recovery)"""
        if not interviewer_question or len(interviewer_question.strip()) < 10:
            return ""

        try:
            messages = self._build_messages(interviewer_question)

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=False
            )

            full_response = response.choices[0].message.content

            # Save to conversation history
            self.history.append({'role': 'user', 'content': interviewer_question})
            self.history.append({'role': 'assistant', 'content': full_response})
            self._trim_history()

            return full_response

        except Exception as e:
            print(f"[ERROR] Local LM Studio sync request failed: {e}")
            print(f"[ERROR] Make sure LM Studio server is running at http://127.0.0.1:1234")
            return ""

    def set_persona(self, new_persona: str):
        """Update the persona and regenerate system prompt"""
        self.persona = new_persona
        self.system_prompt = self._build_system_prompt()
        print(f"[INFO] Persona changed to: {new_persona}")

    def reset_conversation(self):
        """Clear conversation history"""
        self.history = []
        print("[INFO] Conversation history reset")
