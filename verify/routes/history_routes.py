from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database import history_collection
from dependencies import get_current_username

router = APIRouter(prefix="/history", tags=["history"])


class ChatMessage(BaseModel):
    role: str          # "user" or "assistant"
    content: str


class AppendHistoryRequest(BaseModel):
    messages: list[ChatMessage]


@router.get("")
def get_history(username: str = Depends(get_current_username)):
    """Return this signed-in person's own saved conversation history."""
    doc = history_collection.find_one({"username": username})
    messages = doc["messages"] if doc else []
    return {"username": username, "messages": messages}


@router.post("")
def append_history(
    payload: AppendHistoryRequest,
    username: str = Depends(get_current_username),
):
    """Append new messages to this signed-in person's conversation history."""
    new_messages = [
        {
            "role": m.role,
            "content": m.content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        for m in payload.messages
    ]

    history_collection.update_one(
        {"username": username},
        {"$push": {"messages": {"$each": new_messages}}},
        upsert=True,
    )

    return {"message": "History updated", "added": len(new_messages)}


@router.delete("")
def clear_history(username: str = Depends(get_current_username)):
    """Wipe this signed-in person's own conversation history only."""
    history_collection.delete_one({"username": username})
    return {"message": "History cleared"}
