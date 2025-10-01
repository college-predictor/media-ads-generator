from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    message: str
    image_url: str = None  # Optional image URL
    timestamp: str  # ISO formatted timestamp


class Transcript(BaseModel):
    system_behaviour: str = None
    messages: list[ChatMessage]
    llm_model: str = 'gpt-4o'
    temperature: float = 0.7

    def to_openai_format(self) -> list[dict]:
        """Convert transcript to OpenAI chat format"""
        openai_messages = []
        if self.system_behaviour:
            openai_messages.append({"role": "system", "content": self.system_behaviour})
        for msg in self.messages:
            if msg.image_url:
                openai_messages.append({
                    "role": msg.role,
                    "content": [
                        {"type": "input_text", "text": msg.message},
                        {
                            "type": "input_image",
                            "image_url": msg.image_url,
                        },
                    ]
                })
            else:
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.message
                })
        return openai_messages