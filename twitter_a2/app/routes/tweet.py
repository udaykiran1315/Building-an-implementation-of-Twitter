from fastapi import APIRouter, Form, HTTPException
from app.db import tweets
from datetime import datetime

router = APIRouter()

@router.post("/tweet")
def create_tweet(user_id: str = Form(...), content: str = Form(...)):

    if len(content) > 280:
        raise HTTPException(400, "Max 280 chars")

    tweets.insert_one({
        "user_id": user_id,
        "content": content,
        "created_at": datetime.utcnow()
    })

    return {"msg": "Tweet added"}