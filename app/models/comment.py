from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class Comment(BaseModel):
    id: int
    post_id: int
    user_id: str
    parent_comment_id: Optional[int] = None
    content: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    model_config = ConfigDict(from_attributes=True)