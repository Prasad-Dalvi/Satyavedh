"""
FastAPI microservice: the "brain" of the plagiarism checker.

Endpoints:
  POST /analyze   -> upload one image, get back its pHash + CLIP embedding
  POST /compare    -> given two (hash, embedding) pairs, get a similarity verdict

The Node/Express server calls this service; it never talks to MongoDB directly.
Keeping it stateless makes it easy to scale or swap out later.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List

from .hashing import compute_phash
from .embeddings import compute_embedding
from .compare import compare_images
from .ai_detection import detect_ai_generated

app = FastAPI(title="Image Plagiarism Detection Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """
    Accepts an image file, returns its perceptual hash and CLIP embedding.
    Express calls this right after a user uploads an image, then stores
    the result in MongoDB.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()

    try:
        phash = compute_phash(image_bytes)
        embedding = compute_embedding(image_bytes)
        ai_detection = detect_ai_generated(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not process image: {e}")

    return {
        "phash": phash,
        "embedding": embedding,
        "ai_detection": ai_detection,
    }


@app.post("/detect-ai")
async def detect_ai(file: UploadFile = File(...)):
    """
    Standalone AI-generation check, if you ever want to run it without
    also computing hash/embedding (e.g. re-checking an existing image).
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()
    try:
        return detect_ai_generated(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not process image: {e}")


class CompareRequest(BaseModel):
    hash1: str
    hash2: str
    embedding1: List[float]
    embedding2: List[float]


@app.post("/compare")
def compare(req: CompareRequest):
    """
    Compares two already-analyzed images (Express passes stored hash/embedding
    pairs from MongoDB -- no need to re-upload the actual image files).
    """
    result = compare_images(req.hash1, req.hash2, req.embedding1, req.embedding2)
    return result
