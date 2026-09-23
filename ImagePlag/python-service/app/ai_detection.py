"""
AI-generation likelihood detection -- ensemble of 3 open-source classifiers.

A single free detector is unreliable (a 2026 benchmark study found "no
universal winner" among open-source AI-image detectors -- rankings shift
by up to ~20 positions across datasets). Running three independent models
and voting doesn't reach paid-tool accuracy, but it means one model's blind
spot doesn't silently drive the whole verdict, and we can show the person
HOW MANY models agreed instead of a single number pretending to be more
confident than it is.

MODEL_NAMES below is the whole ensemble. Trimming this list to 1-2 entries
is the easiest way to cut the download size (~300-350MB per model) if disk
space is tight -- just remove entries. With only 2 models a 1-1 tie is
possible; the tie-break logic below handles that by summed confidence.
"""

import io
from PIL import Image
from transformers import pipeline

MODEL_NAMES = [
    "umm-maybe/AI-image-detector",
    "Organika/sdxl-detector",
    "dima806/ai_vs_real_image_detection",
]

_classifiers = {}  # model name -> loaded pipeline, populated lazily


def _load_classifier(model_name: str):
    """Lazy-load each model on first use, cached after that."""
    if model_name not in _classifiers:
        _classifiers[model_name] = pipeline("image-classification", model=model_name)
    return _classifiers[model_name]


def _normalize_label(raw_label: str) -> str:
    """
    Different models name their classes differently (e.g. "real" vs "human"
    vs "authentic", or "fake" vs "artificial" vs "generated"). Collapse
    whatever a model calls its classes into our two buckets by keyword,
    rather than assuming an exact string match that might not hold for
    every model in the ensemble.
    """
    label = raw_label.lower()
    if any(k in label for k in ["human", "real", "photo", "authentic"]):
        return "human"
    return "artificial"  # covers "artificial", "fake", "ai", "generated", "synthetic", etc.


def _run_single_model(model_name: str, img: Image.Image) -> dict:
    classifier = _load_classifier(model_name)
    results = classifier(img)  # list of {"label": ..., "score": ...}, sorted desc

    # Collapse into normalized buckets in case a model has more than 2 raw labels
    bucket_scores = {"artificial": 0.0, "human": 0.0}
    for r in results:
        bucket_scores[_normalize_label(r["label"])] += r["score"]

    top_label = max(bucket_scores, key=bucket_scores.get)
    return {
        "model": model_name,
        "label": top_label,
        "confidence": round(bucket_scores[top_label], 4),
    }


def detect_ai_generated(image_bytes: bytes) -> dict:
    """
    Runs every model in MODEL_NAMES and returns an ensemble verdict:
      {
        "label": "artificial" | "human",       # majority vote
        "confidence": 0.81,                     # avg confidence among models that agree with the majority
        "agreement": "2/3",                     # how many models agreed
        "models": [ {model, label, confidence}, ... ]  # full breakdown for transparency
      }
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    per_model = [_run_single_model(name, img) for name in MODEL_NAMES]

    votes = {"artificial": [], "human": []}
    for m in per_model:
        votes[m["label"]].append(m["confidence"])

    # Majority vote; ties broken by which bucket has higher summed confidence
    if len(votes["artificial"]) != len(votes["human"]):
        winner = max(votes, key=lambda k: len(votes[k]))
    else:
        winner = max(votes, key=lambda k: sum(votes[k]))

    winning_confidences = votes[winner]
    avg_confidence = sum(winning_confidences) / len(winning_confidences) if winning_confidences else 0.0

    return {
        "label": winner,
        "confidence": round(avg_confidence, 4),
        "agreement": f"{len(winning_confidences)}/{len(per_model)}",
        "models": per_model,
    }
