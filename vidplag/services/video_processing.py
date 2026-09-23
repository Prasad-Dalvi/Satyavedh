"""Frame analysis and majority-vote aggregation."""

from services.image_analysis import analyze_image


def analyze_frames(frames: list[dict]) -> list[dict]:
    return [
        {
            "frame_index": frame["frame_index"],
            "time_range": frame["time_range"],
            "label": (result := analyze_image(frame["path"]))["label"],
            "confidence": result["confidence"],
        }
        for frame in frames
    ]


def compute_majority(frame_results: list[dict]) -> dict:
    if not frame_results:
        raise ValueError("No frame results to aggregate")
    counts: dict[str, int] = {}
    confidence_totals: dict[str, float] = {}
    for frame in frame_results:
        label = frame["label"]
        counts[label] = counts.get(label, 0) + 1
        confidence_totals[label] = confidence_totals.get(label, 0.0) + frame["confidence"]
    highest_count = max(counts.values())
    tied = [label for label, count in counts.items() if count == highest_count]
    majority_label = max(tied, key=lambda label: confidence_totals[label])
    decisions = {
        "AI-generated": "AI-generated video detected",
        "Real": "Real video detected",
        "Unknown": "Unable to determine video authenticity",
    }
    return {
        "label_counts": counts,
        "majority_label": majority_label,
        "final_decision": decisions.get(majority_label, decisions["Unknown"]),
        "confidence_score": round(confidence_totals[majority_label] / counts[majority_label], 4),
    }
