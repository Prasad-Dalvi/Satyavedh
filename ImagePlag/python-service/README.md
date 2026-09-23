# Python Analysis Service

FastAPI microservice that computes perceptual hashes and CLIP embeddings for images.

## Setup

```bash
cd python-service
python -m venv venv

# Windows PowerShell
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Windows Command Prompt
venv\Scripts\python.exe -m pip install -r requirements.txt

# macOS/Linux
./venv/bin/python -m pip install -r requirements.txt
```

Note: `open_clip_torch` + `torch` download is a few hundred MB on first install
(and the CLIP model weights download on first use of `/analyze`, ~350MB).
This all still costs $0, but needs a decent internet connection once.

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Service runs at `http://localhost:8000`. Check `http://localhost:8000/health`.

**Deploying (Render):** Render injects a `$PORT` env var and expects the service to
bind to it, not a fixed port. Start command there should be:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Endpoints

- `POST /analyze` — form-data with a `file` field (the image). Returns `{ phash, embedding }`.
- `POST /compare` — JSON body `{ hash1, hash2, embedding1, embedding2 }`. Returns similarity verdict.
- Interactive docs at `http://localhost:8000/docs` (FastAPI auto-generates this).
