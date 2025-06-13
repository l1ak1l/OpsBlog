# app/services/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.security import (
    authenticate_user, 
    create_access_token, 
    oauth2_scheme,
    get_current_user
)
from app.models.schemas import UserRegister, UserResponse, Token, UserRole
from app.database.supabase import sb_client  # Import directly
from datetime import timedelta
from app.config import settings
from jose import jwt, JWTError
from supabase import AuthApiError # Corrected import path for AuthApiError

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    # 1. Check if username exists in profiles table to prevent duplicates
    try:
        existing_user_profile = sb_client.table("profiles") \
            .select("user_id") \
            .eq("username", user_data.username) \
            .limit(1).execute()
            
        if existing_user_profile.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    except Exception as e:
        # Catch any unexpected errors during the profile table query
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking existing username: {str(e)}"
        )
    
    # 2. Attempt to create user in Supabase Auth
    try:
        auth_response = sb_client.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "username": user_data.username # Store username in Supabase user metadata
                }
            }
        })
        
        # If sign_up was successful but didn't return a user (unlikely for AuthApiError but good fallback)
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supabase sign-up did not return a user object. This might indicate an issue with the registration data or Supabase configuration."
            )
        
        # 3. Create a corresponding profile entry in your 'profiles' table
        profile_data = {
            "user_id": auth_response.user.id,
            "username": user_data.username,
            # Removed "email": auth_response.user.email from here, as email is handled by Supabase Auth
        }
        
        # Insert the new profile into the 'profiles' table
        sb_client.table("profiles") \
            .insert(profile_data) \
            .execute()
            
        # Return the newly registered user's details
        return UserResponse(
            id=auth_response.user.id,
            email=auth_response.user.email,
            role=UserRole.READER, # Assign a default role upon registration
            created_at=auth_response.user.created_at,
            username=user_data.username,
            avatar_url=None, # Placeholder, can be updated later
            bio=None # Placeholder, can be updated later
        )
    except AuthApiError as e:
        # Handle specific errors returned by the Supabase Auth API
        error_msg = e.message.lower() # Convert message to lowercase for case-insensitive matching
        
        if "user already registered" in error_msg or "email already registered" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered."
            )
        elif "email address" in error_msg and ("invalid" in error_msg or "malformed" in error_msg):
            # This handles the "Invalid email format" error.
            # Includes the original Supabase message for more context.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid email format (Supabase validation error): {e.message}. Please check the email and try again."
            )
        elif "password" in error_msg and ("too weak" in error_msg or "minimum length" in error_msg):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password does not meet requirements: {e.message}"
            )
        else:
            # Catch any other specific Supabase Auth API errors
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supabase authentication error: {e.message}"
            )
    except Exception as e:
        # Catch any other unexpected errors during the sign-up or profile insertion process
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during registration: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh_token(token: str = Depends(oauth2_scheme)):
    # In a real implementation, you'd typically use a dedicated refresh token for this.
    # For simplicity, this example reissues an access token based on the existing (but valid) access token.
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret, 
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: user ID not found."
            )
            
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        new_access_token = create_access_token(
            data={"sub": user_id}, 
            expires_delta=access_token_expires
        )
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or token has expired."
        )
    except Exception as e:
        # Catch any other unexpected errors during token refresh
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during token refresh: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    # Renamed the function to avoid shadowing the imported 'get_current_user' dependency
    return current_user
