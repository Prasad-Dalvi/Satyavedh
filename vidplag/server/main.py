"""
VidPlag — Video Plagiarism / AI-Detection API

This project is the VIDEO extension of the sister "imgplag" image
plagiarism/AI-detection project (imgplag is a separate, sibling project
and is not required to run this one). VidPlag wraps the image detection
logic: it extracts frames from an uploaded video, runs each frame through
the image AI-detection interface (services/image_analysis.py), and
returns a majority-vote verdict for the whole video.
"""
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import database as db
from server.routes import video, image

app = FastAPI(
    title="VidPlag - Video Plagiarism / AI Detection API",
    description=(
        "Video extension of the imgplag image plagiarism/AI-detection "
        "project. Extracts frames from an uploaded video, runs the image "
        "detection logic on each frame, and returns a majority-vote "
        "verdict for the whole video."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prevent_frontend_cache(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.endswith(".html"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


@app.on_event("startup")
def on_startup():
    os.makedirs(os.path.dirname(db.settings.UPLOAD_DIR), exist_ok=True)
    os.makedirs(db.settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(db.settings.FRAMES_DIR, exist_ok=True)
    db.init_db()


app.include_router(video.router)
app.include_router(image.router)

# Simple static frontend (client/index.html) served at "/"
_client_dir = os.path.join(os.path.dirname(__file__), "..", "client")
if os.path.isdir(_client_dir):
    app.mount("/", StaticFiles(directory=_client_dir, html=True), name="client")
