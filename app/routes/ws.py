from fastapi import APIRouter, WebSocket
from app.database.redis import redis_client
import json

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/comments/{post_id}")
async def comment_websocket(websocket: WebSocket, post_id: int):
    await websocket.accept()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"comments:{post_id}")
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                # Handle deletion message
                if "deleted" in data:
                    await websocket.send_json({"action": "delete", "id": data["deleted"]})
                else:
                    await websocket.send_json({"action": "update", "comment": data})
            except Exception as e:
                print(f"Error sending message: {str(e)}")
    
    await pubsub.unsubscribe(f"comments:{post_id}")