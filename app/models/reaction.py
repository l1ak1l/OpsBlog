from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class ReactionType(str, Enum):
    LIKE = "like"
    BOOKMARK = "bookmark"

class Reaction(BaseModel):
    user_id: str
    post_id: int
    type: ReactionType
    created_at: datetime = datetime.now()