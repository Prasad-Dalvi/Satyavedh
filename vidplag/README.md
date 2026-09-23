# VidPlag — Video Plagiarism / AI-Detection API

VidPlag is the **video extension of the imgplag image plagiarism / AI-detection
project**. It does not contain or depend on imgplag's code — it only depends
on a clearly-defined image-analysis interface, so it can be wired up to the
real imgplag service later (or run standalone with a built-in mock analyzer
today).

**How it works:** a video is uploaded → up to 10 frames are extracted from it
→ each frame is passed through the image AI-detection interface (the same
interface imgplag would expose) → the individual frame labels are combined
with a **majority vote** into one final verdict for the video.

Intended layout (as a sister project beside `imgplag`):

```
DeepFake/
├── imgplag/             (the existing image project)
└── vidplag/             <-- this project
    ├── server/
    │   ├── main.py
    │   └── routes/
    ├── services/
    ├── database.py
    ├── client/index.html
    ├── requirements.txt
    ├── .env.example
    ├── start.sh
    └── README.md
```

## 1. Setup

```bash
cd vidplag
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Or just run the whole thing with:

```bash
./start.sh
```

## 2. Run

```bash
cd vidplag
uvicorn server.main:app --reload --port 8001
```

- Frontend: http://localhost:8001/
- Swagger/API docs: http://localhost:8001/docs

## 3. Connecting to the real imgplag project

By default (`IMAGE_SERVICE_URL` empty in `.env`), VidPlag uses a small local
mock analyzer in `services/image_analysis.py` so the whole pipeline is
testable on its own, without imgplag running.

To connect it to the real imgplag Python image detector, set in `.env`:

```
IMAGE_SERVICE_URL=http://localhost:8000/analyze
```

`services/image_analysis.py` will then POST each extracted frame to that
URL and read the nested `ai_detection` result returned by ImagePlag. It maps
ImagePlag's `artificial`/`human` labels to VidPlag's `AI-generated`/`Real`
labels. No other code needs to change.

## 4. API Endpoints

| Method | Path                              | Description |
|--------|-----------------------------------|--------------|
| POST   | `/api/video/upload`               | Upload a video. Validates type, size, and duration (max 5 min). Returns `video_id`. |
| GET    | `/api/video/{video_id}`           | Get stored video metadata. |
| POST   | `/api/video/{video_id}/process`   | Extract frames, run image detection on each, compute majority verdict, save + return the result. |
| GET    | `/api/video/{video_id}/result`    | Get the saved result for an already-processed video. |
| GET    | `/api/video/{video_id}/frames`    | Get extracted frame timestamps + labels for a processed video. |
| POST   | `/api/image/analyze`              | Analyze a single image. Same interface the video pipeline calls internally. |
| POST   | `/api/image/bulk-analyze`         | Analyze multiple images at once. |

### Example result (`/process` or `/result`)

```json
{
  "video_id": "abc123",
  "file_name": "sample.mp4",
  "duration_seconds": 300,
  "frames_analyzed": 10,
  "frame_results": [
    { "frame_index": 1, "time_range": "0-30s", "label": "AI-generated", "confidence": 0.91 }
  ],
  "label_counts": { "AI-generated": 6, "Real": 4 },
  "majority_label": "AI-generated",
  "final_decision": "AI-generated video detected",
  "confidence_score": 0.87
}
```

## 5. Frame sampling rule

- A full 5-minute video is split into 10 fixed 30-second windows
  (0-30s, 30-60s, ..., 270-300s).
  - Frame 1: first available frame in the 0-30s window.
  - Frames 2-10: one randomly chosen frame from within each remaining 30s window.
- A shorter video is split evenly into up to 10 windows across its full
  duration. The first frame comes from the first window; subsequent frames
  are randomly selected inside their windows.
- Videos longer than 5 minutes (300s) are rejected at upload time.

## 6. Majority decision rule

1. Count each label (`AI-generated`, `Real`, `Unknown`) across all analyzed frames.
2. The label with the highest count becomes the video's `majority_label`.
3. If two or more labels tie on count, the tie is broken by whichever tied
   label has the **highest total confidence** summed across its frames.
4. `confidence_score` in the response is the average confidence of the
   frames that voted for the majority label.

## 7. Storage

SQLite (`vidplag/vidplag.db`, created automatically on first run):
- `videos` — uploaded video metadata and processing status.
- `results` — frame results (JSON), label counts, and final decision per video.

Uploaded videos are saved under `uploads/videos/`, extracted frames under
`uploads/frames/{video_id}/`.

## 8. Notes

- Frame extraction uses OpenCV (`opencv-python-headless`).
- This project intentionally has no authentication, queueing, or cloud
  storage — it's kept simple per the project spec. Swap SQLite/local disk
  for a real DB/object storage if you productionize it further.
