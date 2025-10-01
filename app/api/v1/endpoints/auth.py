from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.core.firebase_auth import GoogleAuthBackend
from app.db.redis import SessionManager


router = APIRouter()
security = HTTPBearer()
session_manager = SessionManager()
auth_backend = GoogleAuthBackend.get_instance()


class UserSession(BaseModel):
    uid: str
    email: str

class LoginRequest(BaseModel):
    firebase_token: str

class LoginResponse(BaseModel):
    message: str
    user: dict

class LogoutRequest(BaseModel):
    firebase_token: str

class LogoutResponse(BaseModel):
    message: str

@router.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """Login with Firebase token and create session"""
    try:
        # Check if session already exists
        user_data = await session_manager.get_session(login_request.firebase_token)
        if not user_data:
            # Verify Firebase token and create new session
            user_data = auth_backend.verify_token(login_request.firebase_token)
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Firebase token"
                )            
            # Create session returns the session data dict
            user_data = await session_manager.create_session(login_request.firebase_token, user_data)
        
        return LoginResponse(
            message="success",
            user=user_data,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to login: {str(e)}"
        )

@router.post("/logout", response_model=LogoutResponse)
async def logout(logout_request: LogoutRequest):
    """Logout and invalidate session"""
    try:
        deleted = await session_manager.delete_session(logout_request.firebase_token)

        if deleted:
            return LogoutResponse(message="success")
        else:
            return LogoutResponse(message="success")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout"
        )