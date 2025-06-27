from fastapi import Depends, HTTPException, status
from app.database.supabase import sb_client
from app.database.redis import redis_client
from app.utils.security import get_current_user
from app.models.post import Post, PostStatus
from app.models.schemas import PostCreate, PostResponse
from app.utils import pubsub
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

async def create_post(post_data: PostCreate, user_id: str):
    try:
        # Generate slug
        slug = f"{post_data.title.lower().replace(' ', '-')}-{str(uuid.uuid4())[:8]}"
        
        # Create post
        post = {
            "author_id": user_id,
            "title": post_data.title,
            "slug": slug,
            "content": post_data.content,
            "status": post_data.status.value,
            "scheduled_at": post_data.scheduled_at,
            "views": 0
        }
        
        # Insert into database
        result = sb_client.table("posts").insert(post).execute()
        new_post = result.data[0] if result.data else None
        
        if not new_post:
            raise HTTPException(status_code=500, detail="Failed to create post")
        
        # Add categories
        if post_data.category_ids:
            for category_id in post_data.category_ids:
                sb_client.table("post_categories").insert({
                    "post_id": new_post["id"],
                    "category_id": category_id
                }).execute()
        
        return PostResponse(**new_post)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating post: {str(e)}")

async def get_post_by_id(post_id: int) -> PostResponse:
    # Check cache first
    cached = await redis_client.get(f"post:{post_id}")
    if cached:
        return PostResponse(**json.loads(cached))
    
    try:
        result = sb_client.table("posts").select("*").eq("id", post_id).single().execute()
        post = result.data
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Get categories
        categories = sb_client.table("post_categories").select("categories(name)").eq("post_id", post_id).execute()
        post["categories"] = [cat["categories"] for cat in categories.data]
        
        # Cache for 5 minutes
        await redis_client.setex(f"post:{post_id}", 300, json.dumps(post))
        
        return PostResponse(**post)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching post: {str(e)}")

async def get_post_by_slug(slug: str) -> PostResponse:
    # Check cache first
    cached = await redis_client.get(f"post:slug:{slug}")
    if cached:
        return PostResponse(**json.loads(cached))
    
    try:
        result = sb_client.table("posts").select("*").eq("slug", slug).single().execute()
        post = result.data
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Get categories
        categories = sb_client.table("post_categories").select("categories(name)").eq("post_id", post["id"]).execute()
        post["categories"] = [cat["categories"] for cat in categories.data]
        
        # Cache for 5 minutes
        await redis_client.setex(f"post:slug:{slug}", 300, json.dumps(post))
        
        return PostResponse(**post)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching post: {str(e)}")

async def update_post(post_id: int, post_data: PostCreate, user_id: str):
    try:
        # Verify ownership
        existing = sb_client.table("posts").select("*").eq("id", post_id).single().execute()
        if not existing.data or existing.data["author_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this post")
        
        update_data = {
            "title": post_data.title,
            "content": post_data.content,
            "status": post_data.status.value,
            "scheduled_at": post_data.scheduled_at,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Update post
        result = sb_client.table("posts").update(update_data).eq("id", post_id).execute()
        
        # Update categories
        if post_data.category_ids is not None:
            # Remove existing categories
            sb_client.table("post_categories").delete().eq("post_id", post_id).execute()
            # Add new categories
            for category_id in post_data.category_ids:
                sb_client.table("post_categories").insert({
                    "post_id": post_id,
                    "category_id": category_id
                }).execute()
        
        # Invalidate cache
        await redis_client.delete(f"post:{post_id}")
        if "slug" in existing.data:
            await redis_client.delete(f"post:slug:{existing.data['slug']}")
        
        return PostResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating post: {str(e)}")

async def delete_post(post_id: int, user_id: str):
    try:
        # Verify ownership
        existing = sb_client.table("posts").select("*").eq("id", post_id).single().execute()
        if not existing.data or existing.data["author_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this post")
        
        # Delete post
        sb_client.table("posts").delete().eq("id", post_id).execute()
        
        # Invalidate cache
        await redis_client.delete(f"post:{post_id}")
        if "slug" in existing.data:
            await redis_client.delete(f"post:slug:{existing.data['slug']}")
        
        return {"message": "Post deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting post: {str(e)}")

async def list_posts(page: int = 1, limit: int = 10, status: Optional[str] = None):
    try:
        offset = (page - 1) * limit
        query = sb_client.table("posts").select("*").order("created_at", desc=True)
        
        if status:
            query = query.eq("status", status)
        
        result = query.range(offset, offset + limit - 1).execute()
        return [PostResponse(**post) for post in result.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching posts: {str(e)}")

async def increment_view_count(post_id: int):
    # Increment in Redis
    await redis_client.zincrby("post_views", 1, post_id)
    
    # Check if we need to sync to DB
    sync_counter = await redis_client.incr("view_sync_counter")
    if sync_counter % 100 == 0:  # Sync every 100 views
        await sync_views_to_db()

async def sync_views_to_db():
    views = await redis_client.zrange("post_views", 0, -1, withscores=True)
    for post_id, count in views:
        # Update database
        sb_client.table("posts").update({"views": int(count)}).eq("id", post_id).execute()
    
    # Reset Redis views
    await redis_client.delete("post_views")
    await redis_client.delete("view_sync_counter")