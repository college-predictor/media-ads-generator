from app.services.llm_service import LLMService

class PostGenerator:
    def __init__(self):
        self.llm_service = LLMService()

    async def expand_user_query(self, transcript) -> dict:
        # Retrieve user data from Redis using UID
        expanded_query = await self.llm_service.expand_query(message)