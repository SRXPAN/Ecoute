import os
from typing import Generator, Optional
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    """
    Flexible LLM client manager supporting multiple providers.
    Currently supports: Google Gemini
    """

    def __init__(self, provider: str = "gemini"):
        self.provider = provider.lower()
        self.context = self._load_interview_context()
        self.system_prompt = self._build_system_prompt()

        if self.provider == "gemini":
            self._init_gemini()
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _init_gemini(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")

            genai.configure(api_key=api_key)

            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 300,
            }

            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]

            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                safety_settings=safety_settings,
                system_instruction=self.system_prompt
            )

            self.chat = self.model.start_chat(history=[])

            print("[INFO] Gemini LLM client initialized successfully")

        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
        except Exception as e:
            raise Exception(f"Failed to initialize Gemini client: {e}")

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

CONTENT STRATEGY:
- Reference specific projects, technologies, or achievements from the Context
- Prioritize recent and relevant experience
- Include quantifiable results when available (numbers, percentages, impact)
- Adapt tone to match the question (technical vs behavioral)

EXAMPLES:

Interviewer (English): "Tell me about a time you solved a complex technical problem"
Your response:
• Optimized database queries - reduced latency 60%
• Implemented caching layer with Redis
• Collaborated with DevOps on infrastructure
• Result: handled 10x traffic spike

Interviewer (Polish): "Jakie masz doświadczenie z React?"
Your response:
• 3 lata komercyjnego doświadczenia
• Budowa SPA z React Hooks i Context API
• Integracja z REST API i GraphQL
• Optymalizacja wydajności - lazy loading

Interviewer (Ukrainian): "Розкажіть про ваш досвід роботи в команді"
Your response:
• Agile/Scrum методологія - 2 роки
• Code review та pair programming
• Менторство junior розробників
• Міжфункціональна співпраця з дизайнерами

Remember: Speed and relevance are critical. The user needs instant, scannable talking points."""

        if self.context:
            return base_prompt.format(context=self.context)
        else:
            return base_prompt.format(context="[No context provided - provide general interview guidance]")

    def get_suggestion(self, interviewer_question: str) -> Generator[str, None, None]:
        """
        Get AI suggestion for interviewer's question with streaming response

        Args:
            interviewer_question: The transcribed question from the interviewer

        Yields:
            Tokens of the response as they are generated
        """
        if not interviewer_question or len(interviewer_question.strip()) < 10:
            return

        try:
            if self.provider == "gemini":
                response = self.chat.send_message(
                    interviewer_question,
                    stream=True
                )

                for chunk in response:
                    if chunk.text:
                        yield chunk.text

        except Exception as e:
            print(f"[ERROR] LLM suggestion failed: {e}")
            yield ""

    def get_suggestion_sync(self, interviewer_question: str) -> str:
        """
        Get AI suggestion synchronously (non-streaming)

        Args:
            interviewer_question: The transcribed question from the interviewer

        Returns:
            Complete response as a string
        """
        if not interviewer_question or len(interviewer_question.strip()) < 10:
            return ""

        try:
            if self.provider == "gemini":
                response = self.chat.send_message(interviewer_question)
                return response.text

        except Exception as e:
            print(f"[ERROR] LLM suggestion failed: {e}")
            return ""

    def reset_conversation(self):
        """Reset the conversation history"""
        if self.provider == "gemini":
            self.chat = self.model.start_chat(history=[])
        print("[INFO] LLM conversation history reset")


if __name__ == "__main__":
    # Test the LLM client
    print("Testing LLM Client...")

    client = LLMClient(provider="gemini")

    test_questions = [
        "Tell me about your experience with Python and backend development",
        "Jakie masz doświadczenie z bazami danych?",
        "Розкажіть про ваші найбільші досягнення"
    ]

    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}")

        print("Streaming response:")
        for token in client.get_suggestion(question):
            print(token, end="", flush=True)
        print("\n")
