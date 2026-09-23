"""
Video endpoints.

VidPlag is a video extension of the imgplag image plagiarism/AI-detection
project: this router uploads a video, extracts frames from it, sends each
frame through the image detection interface (services/image_analysis.py),
and returns a majority-vote verdict for the whole video.
"""
import os
import shutil
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException

import database as db
from server.config import settings
from services.frame_extraction import get_video_duration, extract_frames
from services.video_processing import analyze_frames, compute_majority

router = APIRouter(prefix="/api/video", tags=["video"])


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Accepts a video file, validates type/size/duration, and stores it."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            400,
            f"Unsupported file type '{ext}'. Allowed: {sorted(settings.ALLOWED_VIDEO_EXTENSIONS)}",
        )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    video_id = str(uuid.uuid4())
    save_path = os.path.join(settings.UPLOAD_DIR, f"{video_id}{ext}")

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size_bytes = os.path.getsize(save_path)
    max_bytes = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        os.remove(save_path)
        raise HTTPException(400, f"File too large. Max allowed is {settings.MAX_VIDEO_SIZE_MB}MB")

    try:
        duration = get_video_duration(save_path)
    except ValueError as e:
        os.remove(save_path)
        raise HTTPException(400, f"Could not read video file: {e}")

    if duration > settings.MAX_VIDEO_DURATION_SECONDS:
        os.remove(save_path)
        raise HTTPException(
            400,
            f"Video duration ({duration:.1f}s) exceeds the "
            f"{settings.MAX_VIDEO_DURATION_SECONDS}s (5 minute) limit",
        )

    db.insert_video(video_id, file.filename, save_path, duration, size_bytes)

    return {
        "video_id": video_id,
        "file_name": file.filename,
        "duration_seconds": round(duration, 2),
        "size_bytes": size_bytes,
        "status": "uploaded",
    }


@router.get("/{video_id}")
async def get_video_details(video_id: str):
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(404, "Video not found")
    return video


@router.post("/{video_id}/process")
async def process_video(video_id: str):
    """Extracts frames, runs image detection on each, and saves the
    majority-vote result."""
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(404, "Video not found")

    try:
        frames = extract_frames(video["file_path"], video_id, video["duration_seconds"])
        frame_results = analyze_frames(frames)
        majority = compute_majority(frame_results)
    except (OSError, ValueError) as e:
        raise HTTPException(500, f"Processing failed: {e}")

    db.save_result(
        video_id=video_id,
        frames_analyzed=len(frame_results),
        frame_results=frame_results,
        label_counts=majority["label_counts"],
        majority_label=majority["majority_label"],
        final_decision=majority["final_decision"],
        confidence_score=majority["confidence_score"],
    )
    db.update_video_status(video_id, "processed")

    return {
        "video_id": video_id,
        "file_name": video["file_name"],
        "duration_seconds": video["duration_seconds"],
        "frames_analyzed": len(frame_results),
        "frame_results": frame_results,
        "label_counts": majority["label_counts"],
        "majority_label": majority["majority_label"],
        "final_decision": majority["final_decision"],
        "confidence_score": majority["confidence_score"],
    }


@router.get("/{video_id}/result")
async def get_result(video_id: str):
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(404, "Video not found")

    result = db.get_result(video_id)
    if not result:
        raise HTTPException(404, "Video has not been processed yet. Call /process first")

    return {
        "video_id": video_id,
        "file_name": video["file_name"],
        "duration_seconds": video["duration_seconds"],
        "frames_analyzed": result["frames_analyzed"],
        "frame_results": result["frame_results"],
        "label_counts": result["label_counts"],
        "majority_label": result["majority_label"],
        "final_decision": result["final_decision"],
        "confidence_score": result["confidence_score"],
    }


@router.get("/{video_id}/frames")
async def get_frames(video_id: str):
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(404, "Video not found")

    result = db.get_result(video_id)
    if not result:
        raise HTTPException(404, "Video has not been processed yet. Call /process first")

    return {"video_id": video_id, "frames": result["frame_results"]}
