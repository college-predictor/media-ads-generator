#!/usr/bin/env python3
"""
Startup script for the Educational Website API
"""

import uvicorn
import os
from app.config import settings

if __name__ == "__main__":
    print("🚀 Starting Educational Website API")
    print(f"📍 Server will run on {settings.HOST}:{settings.PORT}")
    print(f"🐛 Debug mode: {settings.DEBUG}")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📖 ReDoc Documentation: http://localhost:8000/redoc")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )
