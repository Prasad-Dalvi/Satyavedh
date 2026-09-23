"""Extract representative frames from uploaded videos with OpenCV."""

import math
import os
import random

import cv2

from server.config import settings


def get_video_duration(video_path: str) -> float:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open video file")
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    finally:
        cap.release()
    if fps <= 0 or frame_count <= 0:
        raise ValueError("Could not read video duration")
    return frame_count / fps


def _grab_frame_at(cap: cv2.VideoCapture, fps: float, timestamp: float, path: str) -> bool:
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(timestamp * fps)))
    success, frame = cap.read()
    return bool(success and cv2.imwrite(path, frame))


def extract_frames(video_path: str, video_id: str, duration: float) -> list[dict]:
    if duration <= 0:
        raise ValueError("Video has zero duration")

    output_dir = os.path.join(settings.FRAMES_DIR, video_id)
    os.makedirs(output_dir, exist_ok=True)
    frame_count = min(
        settings.TARGET_FRAME_COUNT,
        max(1, math.ceil(duration / settings.FRAME_WINDOW_SECONDS)),
    )
    window_size = (
        settings.FRAME_WINDOW_SECONDS
        if duration >= settings.MAX_VIDEO_DURATION_SECONDS
        else duration / frame_count
    )

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open video file")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    extracted = []
    try:
        for index in range(frame_count):
            start = index * window_size
            end = min(start + window_size, duration)
            timestamp = start if index == 0 else random.uniform(start, max(start, end - 1 / fps))
            path = os.path.join(output_dir, f"frame_{index + 1}.jpg")
            if not _grab_frame_at(cap, fps, timestamp, path):
                timestamp = start
                if not _grab_frame_at(cap, fps, timestamp, path):
                    continue
            extracted.append(
                {
                    "frame_index": index + 1,
                    "time_range": f"{int(start)}-{int(end)}s",
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "timestamp": round(timestamp, 2),
                    "path": path,
                }
            )
    finally:
        cap.release()

    if not extracted:
        raise ValueError("No frames could be extracted from the video")
    return extracted
