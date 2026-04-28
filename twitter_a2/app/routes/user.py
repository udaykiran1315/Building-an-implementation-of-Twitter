from fastapi import APIRouter
from app.db import users

router = APIRouter()

@router.get("/check-user/{uid}")
def check_user(uid: str):
    user = users.find_one({"firebase_uid": uid})
    if user:
        return {"exists": True}
    return {"exists": False}