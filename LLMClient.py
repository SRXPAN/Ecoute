import os
from typing import Generator
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LLMClient:
    """
    LLM client manager utilizing local LM Studio server via OpenAI-compatible API.
    Optimized for real-time streaming and safe memory management.
    """

    def __init__(self, provider: str = "local"):
        self.provider = provider.lower()
        self.model_name = 'local-model'  # LM Studio ignores this but OpenAI client requires it
        self.context = self._load_interview_context()
        self.system_prompt = self._build_system_prompt()
        self.history = []
        self.max_history_messages = 6  # Keep only last 3 Q&A pairs

        # Connect to local LM Studio server
        self.client = OpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio"  # LM Studio doesn't validate this but OpenAI client requires it
        )

        print(f"[INFO] Local LLM client initialized successfully, connecting to LM Studio at http://127.0.0.1:1234")

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
        base_prompt = """You are a real-time interview teleprompter assistant. Your user is currently in a live job interview.

CONTEXT (User's Background):
{context}

YOUR ROLE:
- Analyze the interviewer's question in real-time
- Provide instant, actionable talking points
- Help the user recall relevant experience from their background

RESPONSE FORMAT (CRITICAL):
- Respond with EXACTLY 3-4 short bullet points
- Each bullet point should be 5-10 words maximum
- Use keywords and key phrases, NOT full sentences
- NO explanations or elaborations
- Just the raw bullet points

LANGUAGE RULE (CRITICAL):
- ALWAYS respond in the EXACT SAME language as the interviewer's question"""
        if self.context:
            return base_prompt.format(context=self.context)
        else:
            return base_prompt.format(context="[No context provided]")

    def _trim_history(self):
        """Keep only the most recent messages to prevent token overflow"""
        if len(self.history) > self.max_history_messages:
            self.history = self.history[-self.max_history_messages:]

    def get_suggestion(self, interviewer_question: str) -> Generator[str, None, None]:
        """Stream AI suggestions token by token"""
        if not interviewer_question or len(interviewer_question.strip()) < 10:
            return

        try:
            messages = [
                {'role': 'system', 'content': self.system_prompt}
            ] + self.history + [
                {'role': 'user', 'content': interviewer_question}
            ]

            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    full_response += token
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
            messages = [
                {'role': 'system', 'content': self.system_prompt}
            ] + self.history + [
                {'role': 'user', 'content': interviewer_question}
            ]

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

    def reset_conversation(self):
        """Clear conversation history"""
        self.history = []
        print("[INFO] Conversation history reset")
