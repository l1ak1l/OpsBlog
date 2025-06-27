# app/models/schemas.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional, Any
from enum import Enum

# Enums moved here to avoid circular imports
class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class UserRole(str, Enum):
    ADMIN = "admin"
    AUTHOR = "author"
    READER = "reader"
    AUTHENTICATED = "authenticated"

class ReactionType(str, Enum):
    LIKE = "like"
    BOOKMARK = "bookmark"

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    username: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    created_at: datetime
    username: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

# Post Schemas
class PostCreate(BaseModel):
    title: str
    content: str
    status: PostStatus = PostStatus.DRAFT
    category_ids: List[int] = []
    scheduled_at: Optional[datetime] = None

class PostResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    status: PostStatus
    author_id: str
    author_username: str
    views: int
    created_at: datetime
    updated_at: datetime
    categories: List[dict]
    like_count: int = 0
    bookmark_count: int = 0
    user_has_liked: bool = False
    user_has_bookmarked: bool = False

# Comment Schemas
class CommentCreate(BaseModel):
    content: str
    parent_comment_id: Optional[int] = None

class CommentResponse(BaseModel):
    id: int
    content: str
    user_id: str
    username: str
    avatar_url: Optional[str]
    created_at: datetime
    replies: List['CommentResponse'] = []

# Fix circular reference
CommentResponse.model_rebuild()

# Analytics Schemas
class PostAnalytics(BaseModel):
    post_id: int
    title: str
    views: int
    likes: int
    bookmarks: int
    comment_count: int
    avg_read_time: float

class TrendAnalytics(BaseModel):
    date: str
    views: int
    likes: int
    new_users: int