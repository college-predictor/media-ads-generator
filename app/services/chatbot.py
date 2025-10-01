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

        # Run image generation in parallel with error handling
        async def generate_single_image(des, index):
            try:
                system_content = Prompts.AD_IMAGE_GENERATION_PROMPT.value
                # Generate image (returns bytes)
                image_bytes = await self.llm_service.generate_image("gpt-5", [{"role": "system", "content": system_content}, {"role": "user", "content": f"Generate image on the basis of this description: {des}"}])
                
                # Convert bytes to base64 string
                base64_image = base64.b64encode(image_bytes).decode('utf-8')
                print(f"Successfully generated image {index + 1}")
                return {"success": True, "image": base64_image, "description": des, "index": index}
            except Exception as e:
                print(f"Failed to generate image {index + 1}: {str(e)}")
                return {"success": False, "error": str(e), "description": des, "index": index}

        # Generate all images in parallel
        image_tasks = [generate_single_image(des, i) for i, des in enumerate(descriptions.descriptions)]
        image_results = await asyncio.gather(*image_tasks, return_exceptions=True)

        # Filter successful image results
        successful_images = []
        for result in image_results:
            if isinstance(result, dict) and result.get("success"):
                successful_images.append(result)
            elif isinstance(result, Exception):
                print(f"Image generation exception: {str(result)}")
        
        print(f"Successfully generated {len(successful_images)} out of {len(descriptions.descriptions)} images")
        
        # Generate captions and tags in parallel for successful images only
        async def generate_caption_with_error_handling(image_data):
            try:
                caption_tags = await self.caption_tags(image_data["image"])
                print(f"Successfully generated caption for image {image_data['index'] + 1}")
                return {"success": True, "caption_tags": caption_tags, "image_data": image_data}
            except Exception as e:
                print(f"Failed to generate caption for image {image_data['index'] + 1}: {str(e)}")
                # Return default caption and tags on failure
                return {
                    "success": False, 
                    "caption_tags": ImageCaptionTags(
                        caption="Amazing advertisement!", 
                        tags=["#ad", "#product", "#marketing", "#brand", "#promotion"]
                    ), 
                    "image_data": image_data,
                    "error": str(e)
                }
        
        caption_tasks = [generate_caption_with_error_handling(img_data) for img_data in successful_images]
        caption_results = await asyncio.gather(*caption_tasks, return_exceptions=True)

        # Filter successful caption results and create templates
        final_templates = []
        successful_captions = 0
        failed_captions = 0
        
        for result in caption_results:
            if isinstance(result, dict):
                image_data = result["image_data"]
                caption_tags = result["caption_tags"]
                
                if result.get("success"):
                    successful_captions += 1
                else:
                    failed_captions += 1
                
                # Create template regardless of caption success (with fallback for failed captions)
                template = {
                    "title": f"Advertisement Template {len(final_templates) + 1}",
                    "description": image_data["description"],
                    "image_url": f"data:image/png;base64,{image_data['image']}",
                    "caption": caption_tags.caption,
                    "tags": caption_tags.tags,
                    "template_number": len(final_templates) + 1,
                    "original_index": image_data["index"]
                }
                
                if not result.get("success"):
                    template["caption_warning"] = "Used default caption due to generation failure"
                
                final_templates.append(template)
        
        # Send progress update
        total_requested = len(descriptions.descriptions)
        total_generated = len(final_templates)
        
        yield {
            "category": "text",
            "role": "assistant",
            "message": f"Successfully generated {total_generated} out of {total_requested} advertisement templates. Images: {len(successful_images)} successful, Captions: {successful_captions} successful, {failed_captions} with fallbacks.",
            "timestamp": datetime.now().isoformat(),
            "loading": False,
        }
        
        # Yield final templates
        yield {
            "templates": final_templates,
            "category": "final_templates",
            "timestamp": datetime.now().isoformat(),
            "loading": False,
            "stats": {
                "total_requested": total_requested,
                "total_generated": total_generated,
                "images_successful": len(successful_images),
                "captions_successful": successful_captions,
                "captions_with_fallback": failed_captions
            }
        }
