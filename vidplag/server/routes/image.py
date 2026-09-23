"""
Image endpoints.

POST /api/image/analyze is the interface the video pipeline uses
internally for every extracted frame (see services/video_processing.py).
It's exposed here directly too, so single images can be tested/analyzed
on their own, and so it can later be swapped for a direct call into the
real imgplag service (see services/image_analysis.py).
"""
import os
import shutil
import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException

from server.config import settings
from services.image_analysis import analyze_image

router = APIRouter(prefix="/api/image", tags=["image"])


def _save_temp_image(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(400, "No file provided")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            400,
            f"Unsupported image type '{ext}'. Allowed: {sorted(settings.ALLOWED_IMAGE_EXTENSIONS)}",
        )
    os.makedirs(settings.FRAMES_DIR, exist_ok=True)
    temp_path = os.path.join(settings.FRAMES_DIR, f"upload_{uuid.uuid4()}{ext}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return temp_path


def _remove_temp(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


@router.post("/analyze")
async def analyze_single_image(file: UploadFile = File(...)):
    path = _save_temp_image(file)
    try:
        result = analyze_image(path)
    finally:
        _remove_temp(path)
    return {"file_name": file.filename, **result}


@router.post("/bulk-analyze")
async def analyze_multiple_images(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        path = _save_temp_image(file)
        try:
            result = analyze_image(path)
        finally:
            _remove_temp(path)
        results.append({"file_name": file.filename, **result})
    return {"results": results}
