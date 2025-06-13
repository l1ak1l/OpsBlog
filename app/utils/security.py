# app/utils/security.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import settings
from app.database.supabase import sb_client  # Import directly
from app.models.schemas import UserRole, UserResponse 
from typing import Optional

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret, 
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt

async def authenticate_user(email: str, password: str) -> Optional[UserResponse]:
    # Get user from Supabase Auth
    try:
        auth_response = sb_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if auth_response.user:
            # Get additional user data from profiles table
            profile_data = sb_client.table("profiles") \
                .select("*") \
                .eq("user_id", auth_response.user.id) \
                .single() \
                .execute()
                
            profile = profile_data.data if profile_data.data else {}
            
            # Create UserResponse instance
            return UserResponse(
                id=auth_response.user.id,
                email=auth_response.user.email,
                role=UserRole(auth_response.user.role or "reader"),
                created_at=auth_response.user.created_at,
                username=profile.get("username", ""),
                avatar_url=profile.get("avatar_url"),
                bio=profile.get("bio")
            )
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret, 
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from Supabase
    try:
        user_data = sb_client.table("profiles") \
            .select("*") \
            .eq("user_id", user_id) \
            .single() \
            .execute()
            
        if not user_data.data:
            raise credentials_exception
            
        # Create UserResponse from database data
        return UserResponse(
            id=user_id,
            email=user_data.data["email"],
            role=UserRole(user_data.data.get("role", "reader")),
            created_at=user_data.data["created_at"],
            username=user_data.data["username"],
            avatar_url=user_data.data.get("avatar_url"),
            bio=user_data.data.get("bio")
        )
    except Exception as e:
        print(f"Error fetching user: {str(e)}")
        raise credentials_exception

async def get_current_active_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    # Add your disabled user logic here if needed
    # For now, just return the user
    return current_user

async def get_admin_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user