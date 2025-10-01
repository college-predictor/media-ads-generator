from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
from datetime import datetime

from app.core.firebase_auth import GoogleAuthBackend
from app.services.connection_manager import ConnectionManager
from app.db.redis import session_manager
from app.services.chatbot import ChatbotService
from app.prompts.prompts import Prompts

router = APIRouter()
security = HTTPBearer()
auth_backend = GoogleAuthBackend.get_instance()

# Global connection manager
manager = ConnectionManager()

chats = {}

# Removed authentication validations - direct UID-based connection

@router.websocket("/ws/{uid}")
async def websocket_endpoint(websocket: WebSocket, uid: str):
    """WebSocket endpoint for chatbot communication using UID"""
    try:
        print(f"WebSocket connection for UID: {uid}")
        
        # Try to get user data from session, otherwise create simple user data
        user_data = await session_manager.get_session(uid)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session. Please log in again."
            )
        print(f"No session found for UID {uid}, using default user data")

        if uid not in chats:
            chats[uid] = ChatbotService(Prompts.INFORMATION_COLLECTION_PROMPT.value)

        chatbot_service: ChatbotService = chats[uid]

        # Connect user with UID
        await manager.connect(websocket, uid, user_data)
        
        # Send welcome message
        welcome_message = {
            "role": "assistant",
            "message": f"Welcome {user_data.get('name')}! Let's generate a perfect advertisement post for you.",
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(welcome_message), uid)
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)

                if message_data.get("template_id", False):
                    template_id = message_data["template_id"]
                    # Fetch and send the template
                    template = await chatbot_service.content_fetcher.fetch_template(template_id)
                    async for response in chatbot_service.generate_templates(template):
                        await manager.send_personal_message(json.dumps(response), uid)
                    
                    await manager.send_personal_message(json.dumps(template), uid)
                else:
                    # Process the message
                    async for response in chatbot_service.process_user_message(message_data.get("message")):
                        # Send response back to client
                        await manager.send_personal_message(json.dumps(response), uid)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                error_message = {
                    "type": "error",
                    "message": "Invalid message format. Please send valid JSON.",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(error_message), uid)
            except Exception as e:
                error_message = {
                    "type": "error",
                    "message": f"An error occurred: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(error_message), uid)
                
    except Exception as e:
        # Handle any errors
        print(f"WebSocket error for UID {uid}: {str(e)}")
        try:
            await websocket.close(code=1011, reason=f"Server error: {str(e)}")
        except:
            pass
    finally:
        # Cleanup
        manager.disconnect(uid)
        print(f"Cleaned up connection for UID: {uid}")
