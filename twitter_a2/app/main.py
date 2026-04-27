from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.db import users
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# ✅ HELPER FUNCTION (VERY IMPORTANT FIX)
def render(template_name: str, request: Request, context: dict = {}):
    context["request"] = request
    return templates.TemplateResponse(
        request,
        template_name,
        context
    )


# 🔐 LOGIN PAGE
@app.get("/")
def login_page(request: Request):
    return render("login.html", request, {})


# 👤 USERNAME PAGE
@app.get("/username")
def username_page(request: Request):
    return render("username.html", request, {"error": None})


# 🔍 CHECK USER
@app.get("/check-user/{uid}")
def check_user(uid: str):
    user = users.find_one({"firebase_uid": uid})
    return {"exists": bool(user)}


# ✅ SET USERNAME
@app.post("/set-username")
def set_username(request: Request, firebase_uid: str = Form(...), username: str = Form(...)):

    # Duplicate username
    if users.find_one({"username": username}):
        return render("username.html", request, {
            "error": "Username already taken. Try another."
        })

    # Already exists
    if users.find_one({"firebase_uid": firebase_uid}):
        return RedirectResponse("/feed", status_code=303)

    # Insert user
    users.insert_one({
        "firebase_uid": firebase_uid,
        "username": username,
        "bio": "",
        "profile_pic": "",
        "following": []
    })

    return RedirectResponse("/feed", status_code=303)


# 🐦 FEED PAGE
@app.get("/feed")
def feed(request: Request):
    return render("feed.html", request, {})


# ▶ RUN WITH BUTTON
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)