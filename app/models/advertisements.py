from pydantic import BaseModel, Field
from typing import List

class AdvertisementTemplate(BaseModel):
    id: str
    title: str
    description: str
    image_url: str

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "image_url": self.image_url,
        }
    

class ImageCaptionTags(BaseModel):
    caption: str
    tags: List[str]

class ImageDescriptions(BaseModel):
    descriptions: List[str] = Field(default_factory=list, description="List of 3 different description of a advertisement post image targetting 3 different audiences in less than 30 words.")

class Post(ImageCaptionTags):
    id: str
    title: str
    content: str
    description: str
    image_url: str
