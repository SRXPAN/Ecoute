import os
from typing import AsyncGenerator, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI
import asyncio

load_dotenv()


class LLMClient:
    """
    LLM client manager utilizing local LM Studio server via OpenAI-compatible API.
    Optimized for real-time streaming and safe memory management.
    GUI-independent version with queue support.
    """

    def __init__(self, provider: str = "local", persona: str = "Short Bullets", llm_queue=None):
        self.provider = provider.lower()
        self.persona = persona
        self.llm_queue = llm_queue  # asyncio.Queue for streaming output
        self.model_name = 'local-model'
        self.context = ""
        self.system_prompt = self._build_system_prompt()
        self.history = []
        self.max_history_messages = 10

        self.client = AsyncOpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio"
        )

        print(f"[INFO] Local LLM client initialized successfully (Persona: {self.persona}), connecting to LM Studio at http://127.0.0.1:1234")

    def _build_system_prompt(self) -> str:
        """
        Dynamically builds the system prompt based on the selected AI persona.
        """
        context_handling_rule = (
            "\n\nCONTEXT HANDLING RULE: You are receiving input from a Live Speech-to-Text tool. "
            "Natural pauses mean a single question might be split across multiple messages. "
            "Do not treat every message as a standalone question. Analyze the current input against previous history. "
            "If it's a fragment or continuation, logically merge it with the previous context to provide one cohesive response."
        )

        if self.persona == "Interview Copilot":
            base_prompt = (
                "You are an expert IT/Project Management interview copilot.\n"
                "CRITICAL RULES (ЖОРСТКІ ПРАВИЛА):\n"
                "1. LANGUAGE MATCHING: You MUST answer in the EXACT SAME LANGUAGE as the interviewer's question. "
                "If the question is in Ukrainian, reply IN UKRAINIAN. If the question is in English, reply IN ENGLISH.\n"
                "2. Keep it EXTREMELY SHORT (максимум 3-5 тез / 3-5 bullet points).\n"
                "3. Keywords and core concepts only. Жодної 'води', вступів чи висновків. No fluff, no intros, no conclusions."
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

        context_str = self.context[:15000] if self.context else "[Контекст не надано / No context provided]"
        return f"{base_prompt}{context_handling_rule}\n\nCONTEXT (Досвід користувача):\n{context_str}"

    def _trim_history(self):
        """Keep only the most recent conversation messages to prevent token overflow."""
        if len(self.history) > self.max_history_messages:
            self.history = self.history[-self.max_history_messages:]

    def _build_messages(self):
        """Always include the system prompt and only the last 10 history messages."""
        recent_history = self.history[-self.max_history_messages:]
        return [
            {'role': 'system', 'content': self.system_prompt}
        ] + recent_history

    async def get_suggestion(self, interviewer_question: str, request_id: Optional[int] = None) -> AsyncGenerator[str, None]:
        """Stream AI suggestions token by token"""
        if not interviewer_question or not interviewer_question.strip():
            return

        # Logically merge fragments: if the last message was from the user, append to it.
        # This happens if the previous suggestion task was cancelled by a newer fragment.
        if self.history and self.history[-1]['role'] == 'user':
            self.history[-1]['content'] += " " + interviewer_question
        else:
            self.history.append({'role': 'user', 'content': interviewer_question})

        try:
            clear_sent = False
            messages = self._build_messages()

            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                max_tokens=200,
                temperature=0.3
            )

            full_response = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content

                    if not clear_sent and self.llm_queue:
                        self.llm_queue.put_nowait({
                            "type": "llm_hint",
                            "text": "",
                            "clear": True,
                            "history_id": request_id,
                        })
                        clear_sent = True

                    full_response += token

                    # Push to async queue if available
                    if self.llm_queue:
                        self.llm_queue.put_nowait({
                            "type": "llm_token",
                            "token": token,
                            "history_id": request_id,
                        })

                    yield token

            # Save assistant response to conversation history
            self.history.append({'role': 'assistant', 'content': full_response})
            self._trim_history()

            # Signal completion
            if self.llm_queue:
                self.llm_queue.put_nowait({
                    "type": "llm_complete",
                    "history_id": request_id,
                })

        except asyncio.CancelledError:
            print("[INFO] LLM stream cancelled by a newer request.")
            raise
        except Exception as e:
            print(f"[ERROR] Local LM Studio streaming failed: {e}")
            print(f"[ERROR] Make sure LM Studio server is running at http://127.0.0.1:1234")

    async def get_suggestion_sync(self, interviewer_question: str) -> str:
        """Non-streaming fallback method (for testing or error recovery)"""
        if not interviewer_question or not interviewer_question.strip():
            return ""

        if self.history and self.history[-1]['role'] == 'user':
            self.history[-1]['content'] += " " + interviewer_question
        else:
            self.history.append({'role': 'user', 'content': interviewer_question})

        try:
            messages = self._build_messages()

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=False,
                max_tokens=200,
                temperature=0.3
            )

            full_response = response.choices[0].message.content

            # Save assistant response to conversation history
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
