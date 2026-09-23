"""
CLIP-based embeddings.

Perceptual hashing catches near-identical images (same pixels, lightly edited).
CLIP embeddings catch a broader kind of similarity: recolored images, heavy
crops, style-similar compositions, or the "same photo re-rendered" case that
pHash can miss. This is heavier to run (loads a neural net) so we load the
model once at startup and reuse it.
"""

import io
import torch
import open_clip
from PIL import Image
import numpy as np

_model = None
_preprocess = None
_device = "cuda" if torch.cuda.is_available() else "cpu"


def _load_model():
    """Lazy-load CLIP so the API starts up fast; model loads on first request."""
    global _model, _preprocess
    if _model is None:
        _model, _, _preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="openai"
        )
        _model.to(_device)
        _model.eval()
    return _model, _preprocess


def compute_embedding(image_bytes: bytes) -> list:
    """
    Returns a normalized embedding vector (list of floats) for an image.
    Store this in MongoDB; compare with cosine similarity later.
    """
    model, preprocess = _load_model()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = preprocess(img).unsqueeze(0).to(_device)

    with torch.no_grad():
        embedding = model.encode_image(tensor)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)  # normalize

    return embedding.squeeze(0).cpu().numpy().tolist()


def cosine_similarity(vec1: list, vec2: list) -> float:
    """
    Cosine similarity between two embeddings, range -1 to 1.
    Since vectors are normalized, this is just a dot product.
    Above ~0.9 usually means very similar images/style; tune this threshold
    with real data once you have a test set.
    """
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b))
