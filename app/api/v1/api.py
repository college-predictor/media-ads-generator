from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    ws
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(ws.router, prefix="/chatbot", tags=["chatbot"])
