from app.db.mongo import mongodb
from app.models.advertisements import AdvertisementTemplate


class ContentFetcher:
    def __init__(self):
        pass

    async def fetch_templates(self, category="general") -> list[AdvertisementTemplate]:
        """Fetch available templates from MongoDB"""
        if mongodb.client is None:
            raise Exception("MongoDB client is not initialized")
        
        templates_collection = mongodb.db.get_collection("advertisement_templates")
        templates = await templates_collection.find().to_list(length=5)
        for template in templates:
            template['_id'] = str(template['_id'])  # Convert ObjectId to string for JSON serialization     
        return templates
    
    async def fetch_template(self, template_id: str) -> dict:
        """Fetch a specific template by ID from MongoDB"""
        if mongodb.client is None:
            raise Exception("MongoDB client is not initialized")
        
        templates_collection = mongodb.db.get_collection("advertisement_templates")
        template = await templates_collection.find_one({"id": template_id})
        if template:
            return template
        else:
            raise Exception(f"Template with ID {template_id} not found")
