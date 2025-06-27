from fastapi import Depends, HTTPException, status
from app.database.supabase import sb_client
from app.database.redis import redis_client
from app.utils.security import get_current_user
from app.utils import pubsub
from app.models.comment import Comment
from app.models.schemas import CommentCreate, CommentResponse
import json
from typing import List

async def create_comment(post_id: int, comment_data: CommentCreate, user_id: str):
    try:
        # Verify post exists
        post = sb_client.table("posts").select("id").eq("id", post_id).single().execute()
        if not post.data:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Create comment
        comment = {
            "post_id": post_id,
            "user_id": user_id,
            "parent_comment_id": comment_data.parent_comment_id,
            "content": comment_data.content
        }
        
        result = sb_client.table("comments").insert(comment).execute()
        new_comment = result.data[0] if result.data else None
        
        if not new_comment:
            raise HTTPException(status_code=500, detail="Failed to create comment")
        
        # Publish real-time update
        await pubsub.publish(f"comments:{post_id}", json.dumps(new_comment))
        
        return CommentResponse(**new_comment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating comment: {str(e)}")

async def get_comments_for_post(post_id: int) -> List[CommentResponse]:
    # Check cache first
    cached = await redis_client.get(f"comments:{post_id}")
    if cached:
        return [CommentResponse(**c) for c in json.loads(cached)]
    
    try:
        # Get top-level comments
        result = sb_client.table("comments").select("*, profiles(username, avatar_url)").eq("post_id", post_id).is_("parent_comment_id", "null").order("created_at", desc=True).execute()
        
        comments = []
        for comment in result.data:
            # Get replies
            replies = sb_client.table("comments").select("*, profiles(username, avatar_url)").eq("parent_comment_id", comment["id"]).order("created_at").execute()
            comment["replies"] = replies.data
            comments.append(comment)
        
        # Cache for 2 minutes
        await redis_client.setex(f"comments:{post_id}", 120, json.dumps(comments))
        
        return [CommentResponse(**c) for c in comments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching comments: {str(e)}")

async def update_comment(comment_id: int, comment_data: CommentCreate, user_id: str):
    try:
        # Verify ownership
        existing = sb_client.table("comments").select("*").eq("id", comment_id).single().execute()
        if not existing.data or existing.data["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this comment")
        
        update_data = {
            "content": comment_data.content,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Update comment
        result = sb_client.table("comments").update(update_data).eq("id", comment_id).execute()
        updated_comment = result.data[0] if result.data else None
        
        # Invalidate cache
        await redis_client.delete(f"comments:{existing.data['post_id']}")
        
        # Publish update
        await pubsub.publish(f"comments:{existing.data['post_id']}", json.dumps(updated_comment))
        
        return CommentResponse(**updated_comment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating comment: {str(e)}")

async def delete_comment(comment_id: int, user_id: str):
    try:
        # Verify ownership
        existing = sb_client.table("comments").select("*").eq("id", comment_id).single().execute()
        if not existing.data or existing.data["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
        
        # Delete comment
        sb_client.table("comments").delete().eq("id", comment_id).execute()
        
        # Invalidate cache
        await redis_client.delete(f"comments:{existing.data['post_id']}")
        
        # Publish deletion
        await pubsub.publish(f"comments:{existing.data['post_id']}", json.dumps({"deleted": comment_id}))
        
        return {"message": "Comment deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting comment: {str(e)}")