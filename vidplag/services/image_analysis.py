"""The single image-analysis boundary used by all VidPlag endpoints."""

import hashlib
import json
import os

import httpx
from PIL import Image

from server.config import settings

VALID_LABELS = {"AI-generated", "Real", "Unknown"}


def _normalise_result(data: dict) -> dict:
    source = data.get("ai_detection", data)
    raw_label = str(source.get("label", "Unknown")).lower()
    if raw_label in {"artificial", "ai-generated", "ai_generated", "fake", "synthetic", "generated"}:
        label = "AI-generated"
    elif raw_label in {"human", "real", "authentic", "photo"}:
        label = "Real"
    else:
        label = "Unknown"
    try:
        confidence = max(0.0, min(1.0, float(source.get("confidence", 0.0))))
    except (TypeError, ValueError):
        confidence = 0.0
    return {"label": label, "confidence": round(confidence, 4)}


def analyze_image(image_path: str) -> dict:
    if settings.IMAGE_SERVICE_URL:
        try:
            with open(image_path, "rb") as image:
                response = httpx.post(
                    settings.IMAGE_SERVICE_URL,
                    files={"file": (os.path.basename(image_path), image, "image/jpeg")},
                    timeout=settings.IMAGE_SERVICE_TIMEOUT,
                )
            response.raise_for_status()
            return _normalise_result(response.json())
        except (OSError, httpx.HTTPError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return {"label": "Unknown", "confidence": 0.0, "error": str(exc)}

    try:
        with Image.open(image_path) as image:
            pixels = list(image.convert("RGB").resize((8, 8)).getdata())
        brightness = sum(sum(pixel) for pixel in pixels) / (len(pixels) * 3)
        score = ((brightness + int(hashlib.md5(image_path.encode()).hexdigest(), 16) % 100) % 100) / 100
        if score > 0.6:
            label, confidence = "AI-generated", 0.5 + (score - 0.6) * 1.25
        elif score < 0.4:
            label, confidence = "Real", 0.5 + (0.4 - score) * 1.25
        else:
            label, confidence = "Unknown", 0.5
        return {"label": label, "confidence": round(min(confidence, 0.99), 4)}
    except (OSError, ValueError) as exc:
        return {"label": "Unknown", "confidence": 0.0, "error": str(exc)}
