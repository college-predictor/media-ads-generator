from app.services.llm_service import OpenAIService
from app.config import settings
from datetime import datetime
from app.db.database import ContentFetcher
from app.prompts.prompts import Prompts
from app.models.advertisements import ImageCaptionTags, ImageDescriptions
import base64
import asyncio

class ChatbotService:
    def __init__(self, system_prompt: str = None):
        self.llm_service = OpenAIService(api_key=settings.OPENAI_API_KEY)
        self.conversation_history = []
        self.system_prompt = system_prompt
        self.content_fetcher = ContentFetcher()
    
    async def process_user_message(self, user_message: str):
        """Process user message and return chatbot response"""
        self.conversation_history.append({"role": "user", "content": user_message})
        response = await self.llm_service.generate_text("gpt-4o", [{"role": "system", "content": self.system_prompt}] + self.conversation_history)
        self.conversation_history.append({"role": "assistant", "content": response})

        yield {
            "category": "text",
            "role": "assistant",
            "message": response,
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "loading": False
        }

        # Suggest templates if certain keywords are detected
        if "READY FOR AD GENERATION" in response:
            print("Triggering template suggestions...")
            yield {
                "category": "text",
                "role": "assistant",
                "message": "Suggesting relevant templates...",
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "loading": True
            }

            yield {
                "templates": await self.content_fetcher.fetch_templates(),
                "category": "template_suggestion",
                "timestamp": datetime.now().isoformat(),
                "loading": False
            }

    async def generate_image(self, template: dict, image_description: str = None):
        print("Generating image for template:", template)
        """Generate image based on the selected template"""
        # Placeholder for image generation logic

        base64_image = await self.llm_service.generate_image("gpt-5", [{"role": "system", "content": template.get("instructions")}, {"role": "user", "content": image_description}])

        return base64_image


    async def caption_tags(self, base64_image: str) -> ImageCaptionTags:
        """Generate caption and tags for the given image URL"""
        system_prompt = Prompts.AD_TEXT_GENERATION_PROMPT.value
        response: ImageCaptionTags = await self.llm_service.generate_structured_output(
            "gpt-4o", 
            [{"role": "system", "content": system_prompt}] + self.conversation_history + [{"role": "user", "content": [
                { "type": "input_text", "text": "Generate caption in less than 15 words and 5 tags for the given image" },
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                },
            ]}], ImageCaptionTags)
        return response

    async def image_descriptions(self, template: dict) -> ImageDescriptions:
        """Generate image descriptions for the given image URL"""
        system_prompt = Prompts.AD_IMAGE_DESCRIPTION_PROMPT.value
        response: ImageDescriptions = await self.llm_service.generate_structured_output(
            "gpt-4o", 
            [{"role": "system", "content": system_prompt}] + self.conversation_history + [{"role": "user", "content": f"Generate 3 different type of images descriptions describing image in text focusing on the conversation motive for platform: {template.get('description')}" }], ImageDescriptions)
        return response

    async def generate_templates(self, template: dict):
        """Generate 3 different advertisement templates based on image instructions"""
        print("generating descriptions")
        descriptions: ImageDescriptions = await self.image_descriptions(template)
        print("descriptions generated:", descriptions)
        yield {
            "category": "text",
            "role": "assistant",
            "message": "Generating templates...",
            "timestamp": datetime.now().isoformat(),
            "loading": False
        }

        # Run image generation in parallel
        async def generate_single_image(des):
            system_content = Prompts.AD_IMAGE_GENERATION_PROMPT.value
            # Generate image (returns bytes)
            image_bytes = await self.llm_service.generate_image("gpt-5", [{"role": "system", "content": system_content}, {"role": "user", "content": f"Generate image on the basis of this description: {des}"}])
            
            # Convert bytes to base64 string
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            return base64_image

        # Generate all images in parallel
        image_tasks = [generate_single_image(des) for des in descriptions.descriptions]
        images = await asyncio.gather(*image_tasks)
        
        # Generate captions and tags in parallel
        caption_tasks = [self.caption_tags(image) for image in images]
        captions_and_tags = await asyncio.gather(*caption_tasks)

        yield {
            "category": "text",
            "role": "assistant",
            "message": f"Generated {len(images)} images",
            "timestamp": datetime.now().isoformat(),
            "loading": True,
        }
        templates = []
        for i in range(len(images)):
            templates.append({
                "title": f"Advertisement Template {i+1}",
                "description": descriptions.descriptions[i],
                "image_url": f"data:image/png;base64,{images[i]}",  # images[i] is already base64 string
                "caption": captions_and_tags[i].caption,
                "tags": captions_and_tags[i].tags,
                "template_number": i + 1
            })
        yield {
            "templates": templates,
            "category": "final_templates",
            "timestamp": datetime.now().isoformat(),
            "loading": False
        }
