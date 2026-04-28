from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.db import users, tweets
from bson import ObjectId
from datetime import datetime
import os

from app.routes import tweet

app = FastAPI()
app.include_router(tweet.router)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# =========================
# HELPER
# =========================
def render(template_name: str, request: Request, context: dict = {}):
    context["request"] = request
    return templates.TemplateResponse(request, template_name, context)


# =========================
# LOGIN
# =========================
@app.get("/")
def login_page(request: Request):
    return render("login.html", request)


# =========================
# USERNAME PAGE
# =========================
@app.get("/username")
def username_page(request: Request):
    return render("username.html", request, {"error": None})


# =========================
# CHECK USER
# =========================
@app.get("/check-user/{uid}")
def check_user(uid: str):
    return {"exists": bool(users.find_one({"firebase_uid": uid}))}


# =========================
# SET USERNAME
# =========================
@app.post("/set-username")
def set_username(request: Request, firebase_uid: str = Form(...), username: str = Form(...)):

    if users.find_one({"username": username}):
        return render("username.html", request, {"error": "Username taken"})

    users.insert_one({
        "firebase_uid": firebase_uid,
        "username": username,
        "bio": "",
        "profile_pic": "",
        "following": []
    })

    return RedirectResponse("/feed", status_code=303)


# =========================
# FEED
# =========================
@app.get("/feed")
def feed(request: Request):

    all_tweets = list(tweets.find().sort("created_at", -1))

    for t in all_tweets:
        t["_id"] = str(t["_id"])

        user = users.find_one({"firebase_uid": t.get("user_id")})

        t["username"] = user["username"] if user else "unknown"
        t["profile_pic"] = user.get("profile_pic", "/static/default.png") if user else "/static/default.png"


        if t.get("retweet"):
            original_user = users.find_one({"firebase_uid": t.get("original_user_id")})
            t["original_username"] = original_user["username"] if original_user else "unknown"
            t["retweet_by"] = t.get("retweet_by", "unknown")

    return render("feed.html", request, {"tweets": all_tweets})


# =========================
#  SEARCH USER
# =========================
@app.get("/search-user")
def search_user(q: str = ""):

    if not q:
        return []

    result = list(users.find({
        "username": {"$regex": f"^{q}", "$options": "i"}
    }, {"_id": 0}))

    return result


# =========================
#  SEARCH TWEET
# =========================
@app.get("/search-tweet")
def search_tweet(q: str = ""):

    if not q:
        return []

    result = list(tweets.find({
        "content": {"$regex": f"^{q}", "$options": "i"}
    }, {"_id": 0}))

    return result


# =========================
# TIMELINE (UPDATED)
# =========================
@app.get("/timeline")
def timeline(request: Request, uid: str = ""):

    if not uid:
        return RedirectResponse("/feed")

    current = users.find_one({"firebase_uid": uid})
    if not current:
        return {"error": "User not found"}

    ids = current.get("following", []) + [uid]

    timeline_tweets = list(
        tweets.find({"user_id": {"$in": ids}})
        .sort("created_at", -1)
        .limit(20)
    )

    for t in timeline_tweets:
        t["_id"] = str(t["_id"])

        user = users.find_one({"firebase_uid": t["user_id"]})

        t["username"] = user["username"] if user else "unknown"
        t["profile_pic"] = user.get("profile_pic", "/static/default.png") if user else "/static/default.png"

        if t.get("retweet"):
            original_user = users.find_one({"firebase_uid": t.get("original_user_id")})
            t["original_username"] = original_user["username"] if original_user else "unknown"
            t["retweet_by"] = t.get("retweet_by", "unknown")

    return render("timeline.html", request, {"tweets": timeline_tweets})

# =========================
#  EDIT TWEET
# =========================
@app.get("/edit-tweet/{id}")
def edit_page(request: Request, id: str):

    try:
        tweet_data = tweets.find_one({"_id": ObjectId(id)})
    except:
        return {"error": "Invalid ID"}

    if not tweet_data:
        return {"error": "Tweet not found"}

    tweet_data["_id"] = str(tweet_data["_id"])

    return render("edit_tweet.html", request, {"tweet": tweet_data})


@app.post("/edit-tweet")
def edit_tweet(tweet_id: str = Form(...), content: str = Form(...)):

    if len(content) > 280:
        return {"error": "Too long"}

    try:
        tweets.update_one(
            {"_id": ObjectId(tweet_id)},
            {"$set": {"content": content}}
        )
    except:
        return {"error": "Update failed"}

    return RedirectResponse("/feed", status_code=303)


# =========================
# BIO
# =========================
@app.post("/update-bio")
def update_bio(user_id: str = Form(...), bio: str = Form(...)):

    if len(bio) > 280:
        return {"error": "Bio too long"}

    users.update_one(
        {"firebase_uid": user_id},
        {"$set": {"bio": bio}}
    )

    return RedirectResponse("/feed", status_code=303)


# =========================
# FOLLOW / UNFOLLOW
# =========================
@app.post("/follow")
def follow(me: str = Form(...), target: str = Form(...)):
    users.update_one({"firebase_uid": me}, {"$addToSet": {"following": target}})
    return RedirectResponse("/feed", status_code=303)


@app.post("/unfollow")
def unfollow(me: str = Form(...), target: str = Form(...)):
    users.update_one({"firebase_uid": me}, {"$pull": {"following": target}})
    return RedirectResponse("/feed", status_code=303)


# =========================
# PROFILE PIC
# =========================
@app.post("/upload-profile")
async def upload_profile(user_id: str = Form(...), file: UploadFile = File(...)):

    if not file or file.filename == "":
        return {"error": "No file"}

    if file.content_type not in ["image/jpeg", "image/png"]:
        return {"error": "Only JPG/PNG allowed"}

    folder = os.path.join(BASE_DIR, "static", "profile")
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, file.filename)

    with open(path, "wb") as f:
        f.write(await file.read())

    users.update_one(
        {"firebase_uid": user_id},
        {"$set": {"profile_pic": f"/static/profile/{file.filename}"}}
    )

    return RedirectResponse("/feed", status_code=303)


# =========================
# PROFILE PAGE
# =========================
@app.get("/profile/{username}")
def profile(request: Request, username: str):

    user = users.find_one({"username": username})

    if not user:
        return {"error": "User not found"}

    user_tweets = list(
        tweets.find({"user_id": user["firebase_uid"]})
        .sort("created_at", -1)
        .limit(10)
    )

    for t in user_tweets:
        t["_id"] = str(t["_id"])

    return render("profile.html", request, {
        "user": user,
        "tweets": user_tweets
    })
# =========================
#  DELETE TWEET
# =========================
@app.post("/delete-tweet")
def delete_tweet(tweet_id: str = Form(...)):
    try:
        tweets.delete_one({"_id": ObjectId(tweet_id)})
    except:
        return {"error": "Delete failed"}

    return RedirectResponse("/feed", status_code=303)

# =========================
#  CREATE TWEET WITH IMAGE
# =========================
@app.post("/tweet-with-image")
async def tweet_with_image(
    user_id: str = Form(...),
    content: str = Form(...),
    file: UploadFile = File(None)
):

    if len(content) > 280:
        return {"error": "Too long"}

    image_path = ""

    if file and file.filename != "":
        if file.content_type not in ["image/jpeg", "image/png"]:
            return {"error": "Only JPG/PNG allowed"}

        folder = os.path.join(BASE_DIR, "static", "tweets")
        os.makedirs(folder, exist_ok=True)

        file_path = os.path.join(folder, file.filename)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        image_path = f"/static/tweets/{file.filename}"

    tweets.insert_one({
        "user_id": user_id,
        "content": content,
        "image": image_path,
        "created_at": datetime.utcnow(),
        "retweet": False
    })

    return RedirectResponse("/feed", status_code=303)

# =========================
#  EDIT TWEET WITH IMAGE
# =========================
@app.post("/edit-tweet-image")
async def edit_tweet_image(
    tweet_id: str = Form(...),
    content: str = Form(...),
    file: UploadFile = File(None)
):

    update_data = {"content": content}

    if file and file.filename != "":
        if file.content_type not in ["image/jpeg", "image/png"]:
            return {"error": "Only JPG/PNG allowed"}

        folder = os.path.join(BASE_DIR, "static", "tweets")
        os.makedirs(folder, exist_ok=True)

        file_path = os.path.join(folder, file.filename)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        update_data["image"] = f"/static/tweets/{file.filename}"

    tweets.update_one(
        {"_id": ObjectId(tweet_id)},
        {"$set": update_data}
    )

    return RedirectResponse("/feed", status_code=303)

@app.post("/retweet")
def retweet(user_id: str = Form(...), tweet_id: str = Form(...)):

    original = tweets.find_one({"_id": ObjectId(tweet_id)})
    user = users.find_one({"firebase_uid": user_id})

    if not original:
        return {"error": "Tweet not found"}

    tweets.insert_one({
        "user_id": user_id,
        "content": original["content"],
        "image": original.get("image", ""),
        "created_at": datetime.utcnow(),


        "retweet": True,
        "retweet_by": user["username"] if user else "unknown",
        "original_user_id": original["user_id"]
    })

    return RedirectResponse("/feed", status_code=303)
    

# =========================
# RUN
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
