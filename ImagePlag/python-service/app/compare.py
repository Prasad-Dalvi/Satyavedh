"""
Combines pHash distance + CLIP cosine similarity into one verdict.
Kept separate from main.py so the "what counts as a match" logic
is easy to tune in one place.
"""

from .hashing import hash_distance
from .embeddings import cosine_similarity


def compare_images(hash1: str, hash2: str, emb1: list, emb2: list) -> dict:
    h_dist = hash_distance(hash1, hash2)
    similarity = cosine_similarity(emb1, emb2)

    # Tunable thresholds -- adjust based on testing against real examples.
    is_near_duplicate = h_dist <= 8          # pixel-level near-duplicate
    is_semantically_similar = similarity >= 0.9  # style/content match

    verdict = "no_match"
    if is_near_duplicate:
        verdict = "near_duplicate"
    elif is_semantically_similar:
        verdict = "similar"

    return {
        "hash_distance": h_dist,
        "cosine_similarity": round(similarity, 4),
        "verdict": verdict,
    }
