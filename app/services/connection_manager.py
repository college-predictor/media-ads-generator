from fastapi import WebSocket
from typing import Dict


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, user_id: str, user_data: dict):
        await websocket.accept()
        
        # If user already has a connection, close the old one
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].close()
                print(f"Closed existing connection for user ID: {user_id}")
            except:
                pass
        
        self.active_connections[user_id] = websocket
        self.user_sessions[user_id] = user_data
        print(f"User {user_data.get('email', 'Unknown')} (UID: {user_id}) connected to chatbot")

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_sessions:
            user_email = self.user_sessions[user_id].get('email', 'Unknown')
            del self.user_sessions[user_id]
            print(f"User {user_email} (UID: {user_id}) disconnected from chatbot")
        else:
            print(f"User {user_id} disconnected from chatbot")

    async def broadcast(self, message: str):
        """Send message to all connected users"""
        if self.active_connections:
            for user_id, websocket in self.active_connections.items():
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    print(f"Failed to send broadcast to {user_id}: {e}")
                    # Remove failed connection
                    try:
                        del self.active_connections[user_id]
                        if user_id in self.user_sessions:
                            del self.user_sessions[user_id]
                    except:
                        pass