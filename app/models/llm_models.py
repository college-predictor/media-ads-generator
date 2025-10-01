from enum import IntEnum
from pydantic import BaseModel


class ProviderType(IntEnum):
    OPENAI = 1
    GEMINI = 2

class LLMModel(BaseModel):
    name: str
    description: str
    model_id: str
    provider: ProviderType
    api_key: str

