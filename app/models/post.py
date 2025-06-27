from enum import Enum
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class PostCategory(BaseModel):
    id: int
    name: str

class Post(BaseModel):
    id: int
    author_id: str
    title: str
    slug: str
    content: str
    status: PostStatus = PostStatus.DRAFT
    scheduled_at: Optional[datetime] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    views: int = 0
    categories: List[PostCategory] = []
    
    model_config = ConfigDict(from_attributes=True)