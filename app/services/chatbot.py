from app.services.llm_service import OpenAIService
from app.config import settings
from datetime import datetime


class ChatbotService:
    def __init__(self):
        self.llm_service = OpenAIService(api_key=settings.OPENAI_API_KEY)
        self.conversation_history = []

    async def process_user_message(self, user_message: str) -> str:
        """Process user message and return chatbot response"""
        self.conversation_history.append({"role": "user", "content": user_message})
        response = await self.llm_service.generate_text("gpt-4o", self.conversation_history)
        self.conversation_history.append({"role": "assistant", "content": response})
        return {
            "role": "assistant",
            "message": response,
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message
        }

    def get_conversation_history(self) -> list:
        """Return the conversation history"""
        return self.conversation_history
