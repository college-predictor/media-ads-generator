from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional, List, Dict
import base64
from openai import AsyncOpenAI
from pydantic import BaseModel


class LLMService(ABC):
    @abstractmethod
    async def generate_structured_output(self, model: str, messages: dict, schema: BaseModel) -> dict:
        """Generate structured output based on the provided schema"""
        pass

    @abstractmethod
    async def generate_image(self, model: str, messages: dict) -> bytes:
        """Generate an image based on the provided prompt"""
        pass

    @abstractmethod
    async def generate_text(self, model: str, messages: dict) -> str:
        """Generate text based on the provided prompt"""
        pass

    @abstractmethod
    async def stream_response(self, model: str, messages: dict) -> AsyncIterator[str]:
        """Stream response in real-time"""
        pass


class OpenAIService(LLMService):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_structured_output(self, model: str, messages: dict, schema: BaseModel) -> dict:
        """Generate structured output using OpenAI's structured output parsing"""
        try:
            
            response = await self.client.responses.parse(
                model=model,
                input=messages,
                text_format=schema,
            )
            
            return response.output_parsed
            
        except Exception as e:
            raise Exception(f"OpenAI structured output generation failed: {str(e)}")

    async def generate_image(self, model: str, messages: dict) -> bytes:
        """Generate image using OpenAI's image generation"""
        try:
            response = await self.client.responses.create(
                model=model,
                input=messages,
                tools=[{"type": "image_generation"}],
            )

            # Extract image data from response
            image_data = [
                output.result
                for output in response.output
                if output.type == "image_generation_call"
            ]
            
            if image_data:
                image_base64 = image_data[0]
                return base64.b64decode(image_base64)
            else:
                raise Exception("No image data found in response")
                
        except Exception as e:
            raise Exception(f"OpenAI image generation failed: {str(e)}")

    async def generate_text(self, model: str, messages: dict) -> str:
        """Generate text using OpenAI"""
        try:
            response = await self.client.responses.create(
                model=model,
                input=messages
            )
            
            return response.output_text
            
        except Exception as e:
            raise Exception(f"OpenAI text generation failed: {str(e)}")

    async def stream_response(self, model: str, messages: dict) -> AsyncIterator[str]:
        """Stream response from OpenAI in real-time"""
        try:
            stream = await self.client.responses.create(
                model=mode,
                input=messages,
                stream=True,
            )

            async for event in stream:
                yield str(event)
                
        except Exception as e:
            raise Exception(f"OpenAI streaming failed: {str(e)}")


# Factory function to create LLM service instances
def create_llm_service(provider: str, api_key: str) -> LLMService:
    """Factory function to create LLM service instances"""
    if provider.lower() == "openai":
        return OpenAIService(api_key)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
