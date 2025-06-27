from fastapi import APIRouter, Depends, Path
from app.services import comment as comment_service
from app.models.schemas import CommentCreate, CommentResponse
from app.utils.security import get_current_user
from typing import List

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.post("/{post_id}", response_model=CommentResponse)
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_user)
):
    return await comment_service.create_comment(post_id, comment_data, current_user.id)

@router.get("/{post_id}", response_model=List[CommentResponse])
async def get_comments_for_post(
    post_id: int = Path(..., title="The ID of the post to get comments for")
):
    return await comment_service.get_comments_for_post(post_id)

@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_user)
):
    return await comment_service.update_comment(comment_id, comment_data, current_user.id)

@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: dict = Depends(get_current_user)
):
    return await comment_service.delete_comment(comment_id, current_user.id)