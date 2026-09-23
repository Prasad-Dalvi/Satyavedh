"""Small SQLite persistence layer for videos and analysis results."""

import json
import sqlite3
from contextlib import contextmanager

from server.config import settings


@contextmanager
def get_conn():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY, file_name TEXT NOT NULL, file_path TEXT NOT NULL,
            duration_seconds REAL NOT NULL, size_bytes INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'uploaded', created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS results (
            video_id TEXT PRIMARY KEY, frames_analyzed INTEGER NOT NULL, frame_results TEXT NOT NULL,
            label_counts TEXT NOT NULL, majority_label TEXT NOT NULL, final_decision TEXT NOT NULL,
            confidence_score REAL NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos (video_id)
        )""")


def insert_video(video_id, file_name, file_path, duration_seconds, size_bytes):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO videos (video_id, file_name, file_path, duration_seconds, size_bytes) VALUES (?, ?, ?, ?, ?)",
            (video_id, file_name, file_path, duration_seconds, size_bytes),
        )


def get_video(video_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,)).fetchone()
        return dict(row) if row else None


def update_video_status(video_id, status):
    with get_conn() as conn:
        conn.execute("UPDATE videos SET status = ? WHERE video_id = ?", (status, video_id))


def save_result(video_id, frames_analyzed, frame_results, label_counts, majority_label, final_decision, confidence_score):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO results
            (video_id, frames_analyzed, frame_results, label_counts, majority_label, final_decision, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
            frames_analyzed=excluded.frames_analyzed, frame_results=excluded.frame_results,
            label_counts=excluded.label_counts, majority_label=excluded.majority_label,
            final_decision=excluded.final_decision, confidence_score=excluded.confidence_score""",
            (video_id, frames_analyzed, json.dumps(frame_results), json.dumps(label_counts),
             majority_label, final_decision, confidence_score),
        )


def get_result(video_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM results WHERE video_id = ?", (video_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["frame_results"] = json.loads(result["frame_results"])
        result["label_counts"] = json.loads(result["label_counts"])
        return result
