"""
LLM Configuration and Setup
"""

import os
from typing import Dict, Any
from app.services.llm_service import create_llm_service, LLMService
from app.models.llm_models import LLMModel, ProviderType


class LLMConfig:
    """Configuration class for LLM services"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Available models configuration
        self.models = {
            "gpt-4o": LLMModel(
                name="gpt-4o-2024-08-06",
                description="GPT-4 Optimized model for structured output",
                model_id="gpt-4o-2024-08-06",
                provider=ProviderType.OPENAI,
                api_key=self.openai_api_key or ""
            ),
            "gpt-5": LLMModel(
                name="gpt-5",
                description="GPT-5 model for advanced text generation",
                model_id="gpt-5",
                provider=ProviderType.OPENAI,
                api_key=self.openai_api_key or ""
            ),
            "gemini-pro": LLMModel(
                name="gemini-pro",
                description="Google Gemini Pro model",
                model_id="gemini-pro",
                provider=ProviderType.GEMINI,
                api_key=self.gemini_api_key or ""
            )
        }
        
        # Service instances cache
        self._services: Dict[str, LLMService] = {}
    
    def get_service(self, provider: str) -> LLMService:
        """Get or create LLM service instance"""
        if provider not in self._services:
            if provider.lower() == "openai":
                if not self.openai_api_key:
                    raise ValueError("OpenAI API key not found in environment variables")
                self._services[provider] = create_llm_service("openai", self.openai_api_key)
            elif provider.lower() == "gemini":
                if not self.gemini_api_key:
                    raise ValueError("Gemini API key not found in environment variables")
                self._services[provider] = create_llm_service("gemini", self.gemini_api_key)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        
        return self._services[provider]
    
    def get_model(self, model_name: str) -> LLMModel:
        """Get model configuration by name"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found. Available models: {list(self.models.keys())}")
        return self.models[model_name]
    
    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        """List all available models with their configurations"""
        return {
            name: {
                "name": model.name,
                "description": model.description,
                "provider": model.provider.name,
                "has_api_key": bool(model.api_key)
            }
            for name, model in self.models.items()
        }


# Global configuration instance
llm_config = LLMConfig()


# Convenience functions
def get_openai_service() -> LLMService:
    """Get OpenAI service instance"""
    return llm_config.get_service("openai")


def get_gemini_service() -> LLMService:
    """Get Gemini service instance"""
    return llm_config.get_service("gemini")


def get_model_by_name(model_name: str) -> LLMModel:
    """Get model configuration by name"""
    return llm_config.get_model(model_name)


def list_models() -> Dict[str, Dict[str, Any]]:
    """List all available models"""
    return llm_config.list_available_models()