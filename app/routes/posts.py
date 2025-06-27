from fastapi import APIRouter, Depends, Path, Query, HTTPException
from app.services import post as post_service
from app.models.schemas import PostCreate, PostResponse
from app.utils.security import get_current_user
from typing import List, Optional

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.post("/", response_model=PostResponse)
async def create_post(
    post_data: PostCreate, 
    current_user: dict = Depends(get_current_user)
):
    return await post_service.create_post(post_data, current_user.id)

@router.get("/{post_id}", response_model=PostResponse)
async def get_post_by_id(
    post_id: int = Path(..., title="The ID of the post to get"),
    increment_view: bool = Query(False, description="Increment view count")
):
    post = await post_service.get_post_by_id(post_id)
    if increment_view:
        await post_service.increment_view_count(post_id)
    return post

@router.get("/slug/{slug}", response_model=PostResponse)
async def get_post_by_slug(
    slug: str = Path(..., title="The slug of the post to get"),
    increment_view: bool = Query(False, description="Increment view count")
):
    post = await post_service.get_post_by_slug(slug)
    if increment_view:
        await post_service.increment_view_count(post.id)
    return post

@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int, 
    post_data: PostCreate,
    current_user: dict = Depends(get_current_user)
):
    return await post_service.update_post(post_id, post_data, current_user.id)

@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    current_user: dict = Depends(get_current_user)
):
    return await post_service.delete_post(post_id, current_user.id)

@router.get("/", response_model=List[PostResponse])
async def list_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None)
):
    return await post_service.list_posts(page, limit, status)