from redis.asyncio import from_url
from app.config import settings
import json
import hashlib
from datetime import timedelta

redis = from_url(settings.REDIS_URL, decode_responses=True)

async def get_redis():
    return redis

class SessionManager:
    def __init__(self):
        self.redis_client = redis
        self.session_ttl = 3600  # 24 hours in seconds
    
    async def create_session(self, firebase_token: str, user_data: dict) -> dict:
        """Create a new session and store in Redis"""
        
        session_data = {
            "name": user_data["name"],
            "email": user_data["email"],
            "uid": user_data["uid"],
        }
        
        # Store session data in Redis with TTL
        await self.redis_client.setex(
            firebase_token,
            self.session_ttl,
            json.dumps(session_data)
        )

        # Store session data in Redis with TTL
        await self.redis_client.setex(
            user_data.get("uid"),
            self.session_ttl,
            json.dumps(session_data)
        )
        return session_data
    
    async def get_session(self, firebase_token: str) -> dict:
        """Retrieve session data from Redis"""
        session_data = await self.redis_client.get(firebase_token)
        if session_data:
            return json.loads(session_data)
        return None
    
    async def delete_session(self, firebase_token: str) -> bool:
        """Delete session from Redis"""
        result = await self.redis_client.delete(firebase_token)
        return result > 0

    async def extend_session(self, firebase_token: str) -> bool:
        """Extend session TTL"""
        session_data = await self.get_session(firebase_token)
        if session_data:
            result = await self.redis_client.expire(firebase_token, self.session_ttl)
            return result
        return False

    async def get_data_by_uid(self, uid: str) -> dict:
        """Retrieve session data from Redis using UID"""
        session_data = await self.redis_client.get(uid)
        if session_data:
            return json.loads(session_data)
        return None
    
class ChatSessionManager:
    def __init__(self):
        self.redis_client = redis
        self.chat_ttl = 600  # 7 days in seconds
    
    def _get_chat_key(self, uid: str) -> str:
        return f"chat:{uid}"
    
    async def store_chatbot_instance(self, uid: str, chatbot_instance_id: str) -> bool:
        """Store ChatbotService instance ID for a user"""
        chat_key = self._get_chat_key(uid)
        result = await self.redis_client.setex(
            chat_key,
            self.chat_ttl,
            chatbot_instance_id
        )
        return result
    
    async def get_chatbot_instance(self, uid: str) -> str:
        """Retrieve ChatbotService instance ID for a user"""
        chat_key = self._get_chat_key(uid)
        instance_id = await self.redis_client.get(chat_key)
        return instance_id
    
    async def remove_chatbot_instance(self, uid: str) -> bool:
        """Remove ChatbotService instance ID for a user"""
        chat_key = self._get_chat_key(uid)
        result = await self.redis_client.delete(chat_key)
        return result > 0
    
    async def extend_chat_session(self, uid: str) -> bool:
        """Extend chat session TTL"""
        chat_key = self._get_chat_key(uid)
        result = await self.redis_client.expire(chat_key, self.chat_ttl)
        return result

session_manager = SessionManager()
chat_session_manager = ChatSessionManager()
