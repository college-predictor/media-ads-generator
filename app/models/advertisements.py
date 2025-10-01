from pydantic import BaseModel
from typing import List

class AdvertisementTemplate(BaseModel):
    id: str
    title: str
    description: str
    image_url: str
    embedding_code: List[float]

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "image_url": self.image_url,
            "embedding_code": self.embedding_code,
        }
    

class Post(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str]
    description: str = ""
    image_url: str = ""

    def to_dict(self):
        return {
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "description": self.description,
            "image_url": self.image_url,
        }