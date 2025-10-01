from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from app.api.v1.api import api_router
from app.config import settings
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.db.redis import redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🔄 Connecting to MongoDB...")
    try:
        await connect_to_mongo()
        print("✅ MongoDB connection established successfully!")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise
    
    print("🔄 Connecting to Redis...")
    try:
        # Test Redis connection
        await redis.ping()
        print("✅ Redis connection established successfully!")
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🔄 Closing MongoDB connection...")
    await close_mongo_connection()
    print("✅ MongoDB connection closed successfully!")
    
    print("🔄 Closing Redis connection...")
    try:
        await redis.aclose()
        print("✅ Redis connection closed successfully!")
    except Exception as e:
        print(f"⚠️ Error closing Redis connection: {e}")

app = FastAPI(
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")



@app.get("/")
async def root():
    return {"message": "Media Ad Generator Website API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint that verifies MongoDB and Redis connections"""
    health_status = {"status": "healthy"}
    
    # Check MongoDB connection
    try:
        from app.db.mongo import mongodb
        if mongodb.client is None:
            health_status["database"] = "disconnected"
            health_status["status"] = "unhealthy"
        else:
            # Test database connection
            await mongodb.client.admin.command('ping')
            health_status["database"] = "connected"
            health_status["database_name"] = settings.DATABASE_NAME
    except Exception as e:
        health_status["database"] = "error"
        health_status["database_error"] = str(e)
        health_status["status"] = "unhealthy"
    
    # Check Redis connection
    try:
        await redis.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = "error"
        health_status["redis_error"] = str(e)
        health_status["status"] = "unhealthy"
    
    return health_status

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )