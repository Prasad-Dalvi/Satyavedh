"""
Config for VidPlag.

VidPlag is the VIDEO extension of the sister "imgplag" image plagiarism /
AI-detection project. It does not depend on imgplag's code — it only
depends on an image-analysis interface (see services/image_analysis.py)
that can later be pointed at the real imgplag service.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")


class Settings:
    # --- Video rules ---
    MAX_VIDEO_DURATION_SECONDS = 300  # 5 minutes, per spec
    MAX_VIDEO_SIZE_MB = 200
    ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

    # --- Image rules (for /api/image endpoints) ---
    ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

    # --- Frame sampling rules ---
    TARGET_FRAME_COUNT = 10
    FRAME_WINDOW_SECONDS = 30

    # --- Storage ---
    UPLOAD_DIR = str(PROJECT_DIR / "uploads" / "videos")
    FRAMES_DIR = str(PROJECT_DIR / "uploads" / "frames")
    DB_PATH = str(PROJECT_DIR / "vidplag.db")

    # --- Connection to the sister imgplag service ---
    # If set, each extracted frame is POSTed to this URL for AI-label
    # analysis (this is how VidPlag "wraps" imgplag). If left empty, a
    # local mock analyzer is used so the project runs standalone.
    IMAGE_SERVICE_URL = os.getenv("IMAGE_SERVICE_URL", "")
    IMAGE_SERVICE_TIMEOUT = float(os.getenv("IMAGE_SERVICE_TIMEOUT", "10"))


settings = Settings()
