from enum import Enum
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserRole(str, Enum):
    ADMIN = "admin"
    AUTHOR = "author"
    READER = "reader"

class UserProfile(BaseModel):
    user_id: str
    username: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        from_attributes = True