from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Comment(BaseModel):
    id: int
    post_id: int
    user_id: str
    parent_comment_id: Optional[int] = None  # For threading
    content: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        orm_mode = True