"""
Perceptual hashing utilities.

Perceptual hashes let us detect near-duplicate images (resized, recompressed,
slightly cropped, watermarked, etc.) by comparing hash "distance" instead of
raw pixels. Small distance = visually similar image.
"""

import imagehash
from PIL import Image
import io


def compute_phash(image_bytes: bytes) -> str:
    """
    Compute a perceptual hash (pHash) for an image.
    Returns the hash as a hex string so it can be stored easily in MongoDB.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    phash = imagehash.phash(img)
    return str(phash)


def hash_distance(hash1: str, hash2: str) -> int:
    """
    Hamming distance between two perceptual hashes.
    0 = identical, higher = more different.
    Typical rule of thumb: distance <= 5 usually means "same or near-duplicate image".
    """
    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)
    return h1 - h2
