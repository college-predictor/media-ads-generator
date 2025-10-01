from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional
from app.config import settings


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Initialize MongoDB connection and Beanie"""
    try:
        print(f"📡 Connecting to MongoDB at: {settings.MONGODB_URL}")
        mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongodb.db = mongodb.client[settings.DATABASE_NAME]
        
        # Test the connection
        await mongodb.client.admin.command('ping')
        print(f"🗄️  Connected to database: {settings.DATABASE_NAME}")
        
        # Initialize Beanie with all document models
        print("🔧 Initializing Beanie ODM...")
        await init_beanie(
            database=mongodb.db,
            document_models=[]
        )
        print("✅ Beanie ODM initialized successfully!")
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise e

async def close_mongo_connection():
    if mongodb.client:
        mongodb.client.close()