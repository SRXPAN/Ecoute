import os
from typing import Generator
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

class LLMClient:
    """
    LLM client manager utilizing Ollama for cloud/local models.
    Optimized for GLM-5.1:cloud with real-time streaming.
    """

    def __init__(self, provider: str = "ollama"):
        self.provider = provider.lower()
        self.model_name = 'glm-5.1:cloud'
        self.context = self._load_interview_context()
        self.system_prompt = self._build_system_prompt()
        self.history = []

        print(f"[INFO] Ollama LLM client initialized successfully with model: {self.model_name}")

    def _load_interview_context(self) -> str:
        """Load interview context from temp_context.txt"""
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

        print("[WARNING] No interview context found - responses may be generic")
        return ""

    def _build_system_prompt(self) -> str:
        """Build optimized system prompt for interview assistance"""
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
- NO introductory phrases like "Here are some points:" or "You could mention:"
- NO explanations or elaborations
- Just the raw bullet points

LANGUAGE RULE (CRITICAL):
- ALWAYS respond in the EXACT SAME language as the interviewer's question
- If question is in English → bullets in English
- If question is in Polish → bullets in Polish
- If question is in Ukrainian → bullets in Ukrainian
- If question is in Spanish → bullets in Spanish
- Match the language AUTOMATICALLY without being asked

EXAMPLES:

Interviewer (English): "Tell me about a time you solved a complex technical problem"
Your response:
• Optimized database queries - reduced latency 60%
• Implemented caching layer with Redis
• Collaborated with DevOps on infrastructure
• Result: handled 10x traffic spike

Remember: Speed and relevance are critical. The user needs instant, scannable talking points."""

        if self.context:
            return base_prompt.format(context=self.context)
        else:
            return base_prompt.format(context="[No context provided - provide general interview guidance]")

    def get_suggestion(self, interviewer_question: str) -> Generator[str, None, None]:
        """Get AI suggestion for interviewer's question with streaming response"""
        if not interviewer_question or len(interviewer_question.strip()) < 10:
            return

        try:
            messages = [
                {'role': 'system', 'content': self.system_prompt}
            ] + self.history + [
                {'role': 'user', 'content': interviewer_question}
            ]

            stream = chat(
                model=self.model_name,
                messages=messages,
                stream=True
            )

            full_response = ""
            for chunk in stream:
                token = chunk.message.content
                if token:
                    full_response += token
                    yield token

            self.history.append({'role': 'user', 'content': interviewer_question})
            self.history.append({'role': 'assistant', 'content': full_response})

        except Exception as e:
            print(f"[ERROR] Ollama streaming suggestion failed: {e}")
            yield ""

    def get_suggestion_sync(self, interviewer_question: str) -> str:
        """Get AI suggestion synchronously (non-streaming backup)"""
        if not interviewer_question or len(interviewer_question.strip()) < 10:
            return ""

        try:
            messages = [
                {'role': 'system', 'content': self.system_prompt}
            ] + self.history + [
                {'role': 'user', 'content': interviewer_question}
            ]

            response = chat(
                model=self.model_name,
                messages=messages,
                stream=False
            )

            reply = response.message.content
            self.history.append({'role': 'user', 'content': interviewer_question})
            self.history.append({'role': 'assistant', 'content': reply})
            return reply

        except Exception as e:
            print(f"[ERROR] Ollama sync suggestion failed: {e}")
            return ""

    def reset_conversation(self):
        """Reset the conversation history"""
        self.history = []
        print("[INFO] Ollama conversation history reset")
