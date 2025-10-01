from app.services.llm_service import OpenAIService
from app.config import settings
from app.prompts.prompts import Prompts

class PostGenerator:
    def __init__(self):
        self.llm_service = OpenAIService(api_key=settings.OPENAI_API_KEY)

    

    async def post_description(self, transcript) -> dict:
        # Retrieve user data from Redis using UID
        system_content = Prompts.AD_TEXT_GENERATION_PROMPT.value.format(product_description=transcript)
        expanded_query = await self.llm_service.expand_query(transcript)