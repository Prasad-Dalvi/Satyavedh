# Image Plagiarism Checker (MERN + Python)

Checks uploaded images against a database of previously uploaded images for
near-duplicates (perceptual hash) and style/content similarity (CLIP embeddings).
Zero-cost stack — no paid APIs required.

## Architecture

```
React (client) --> Express (server) --> Python/FastAPI (python-service)
                          |
                      MongoDB
```

- **client/** — React (Vite) upload UI
- **server/** — Express API: handles uploads, talks to Mongo + Python service
- **python-service/** — FastAPI: computes perceptual hash + CLIP embedding, compares two images

## Run order

You need 3 terminals running at once.

### 1. Python service (port 8000)
```bash
cd python-service
python -m venv venv

# Windows PowerShell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# macOS/Linux
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

### 2. MongoDB
Easiest zero-cost option: create a free MongoDB Atlas cluster (atlas.mongodb.com,
free M0 tier) and copy its connection string. Or run MongoDB locally if installed.

### 3. Express server (port 5000)
```bash
cd server
cp .env.example .env   # then edit MONGO_URI inside .env
npm install
npm run dev
```

### 4. React client (port 3000)
```bash
cd client
npm install
npm run dev
```

Open http://localhost:3000 — upload an image, and it'll be compared against
everything already stored. Upload the same image (or a cropped/recolored
version) twice to see a match get flagged.

## Deploying (one container, one URL, free — Hugging Face Spaces)

Everything — Python AI service, Express API, and the built React app — runs
in a **single Docker container** (see `Dockerfile` / `start.sh` at the
project root). Express is the only public process; it serves the API *and*
the built React app itself, and talks to Python internally over
`localhost:8000`. One deployment, one URL, nothing else to stand up.

**Why Hugging Face Spaces:** its free CPU tier gives 16GB RAM and 2 vCPUs at
no cost, permanently — not a trial — with no credit card required. That's
enough headroom for CLIP + 3 AI-detection models, which a typical free-tier
web host (512MB-1GB) can't hold.

### 1. MongoDB Atlas
atlas.mongodb.com → free M0 cluster → Database Access (add a user) →
Network Access (allow `0.0.0.0/0` for simplicity) → Connect → copy the
`mongodb+srv://...` connection string.

### 2. Create the Space (dashboard only, no CLI)
1. huggingface.co → sign up/log in → New → Space
2. Give it a name, choose **Docker** as the Space SDK, choose **Public** or
   **Private**, hardware stays on the free **CPU basic** tier
3. Once created, go to the **Files** tab → **Add file → Upload files** →
   drag your whole project folder in (the `Dockerfile` needs to end up at
   the repo root)
4. Go to **Settings → Variables and secrets** → add a secret:
   - `MONGO_URI` = your Atlas connection string
   (leave `PYTHON_SERVICE_URL` alone — it's already set inside the Dockerfile)
5. The Space builds automatically on upload. Watch the **Logs** tab — first
   build is slow (installing torch/transformers, ~1GB); after that it's
   cached. Once it says "Running", your app is live at
   `https://<your-username>-<space-name>.hf.space`

### 3. Keep it awake with UptimeRobot (free)
Free Spaces sleep after 48 hours with no visits — not billed, just paused,
and the next visitor wakes it back up with a short delay. To avoid that
delay entirely for anyone checking the project out:

1. uptimerobot.com → sign up (free plan)
2. Add New Monitor → **HTTP(s)** → paste your Space URL + `/ping`
   (e.g. `https://<your-username>-<space-name>.hf.space/ping`) — this hits
   the dedicated lightweight endpoint in `server.js` that just confirms the
   container is alive, without touching Python or loading any AI model
3. Set the check interval to **every 5 minutes** (free plan's minimum) —
   comfortably under the 48-hour sleep threshold
4. Save. UptimeRobot now pings the Space regularly, keeping it awake
   indefinitely at no cost.

That's it — one link, always warm, still free.

### Known limitations, worth knowing upfront
- **Disk isn't persistent.** Uploaded images in `server/uploads` are wiped
  on rebuild/restart. Fine for a demo; persisting uploads long-term would
  mean switching to Cloudinary or S3 later.
- Hugging Face's free-tier terms can shift over time — worth a quick check
  of huggingface.co/pricing before relying on this beyond a personal project.
- UptimeRobot's free plan pings publicly reachable URLs only — fine here
  since the Space is public, but keep that in mind if you ever make it private.

## How matching works

1. On upload, Express sends the file to Python's `/analyze` endpoint.
2. Python returns a perceptual hash (pixel-level fingerprint), a CLIP
   embedding (semantic/style fingerprint), and an AI-generation estimate.
3. Express compares the new image against every existing image in MongoDB by
   calling Python's `/compare` endpoint for each pair.
4. Results are tagged:
   - `near_duplicate` — hash distance is low (same image, lightly edited)
   - `similar` — CLIP cosine similarity is high (recolored, cropped, or
     stylistically close)
   - `no_match` — neither threshold triggered

Thresholds live in `python-service/app/compare.py` — tune them once you have
real test images (start with the given defaults: hash distance ≤ 8, cosine
similarity ≥ 0.9).

## AI-generation detection (separate from duplicate matching)

Each upload is run through an **ensemble of three open-source classifiers**
pulled from Hugging Face (no API key or cost):
- `umm-maybe/AI-image-detector`
- `Organika/sdxl-detector`
- `dima806/ai_vs_real_image_detection`

They vote, and the response includes both the majority verdict and the full
per-model breakdown (so you can see when models disagree, not just a single
number). This is a **different problem** from duplicate detection: it looks
at statistical artifacts within a single image rather than comparing it to
anything else.

Why an ensemble instead of one model: a 2026 benchmark study of open-source
AI-image detectors found no consistent best performer — rankings shift
dramatically across image types and generators. Voting across three
independently-trained models means one model's blind spot doesn't silently
drive the whole verdict.

Important limitations, surfaced directly in the UI, not just here:
- Even the ensemble is meaningfully less accurate than paid detection APIs
  (Hive, Sightengine) — treat it as one signal, never a definitive verdict.
- It's especially unreliable on photorealistic images from newer generators,
  which these open-source models weren't trained to catch.
- First call downloads all three models (~1GB total) — expect the first
  upload after starting the Python service to be slow. If disk space is
  tight, trim `MODEL_NAMES` in `python-service/app/ai_detection.py` down to
  1-2 entries; with 2 models a tie is possible and is broken by summed
  confidence.

## Known limitations (by design, to stay free)

- Only compares against images already uploaded to **this** database — it does
  not search the whole internet. Adding whole-web reverse search later would
  require a paid API (Google Vision, TinEye, Bing Visual Search).
- Comparing against every existing image (O(n) per upload) is fine for a
  prototype/small dataset; at scale you'd want a vector index (e.g. FAISS or
  MongoDB Atlas Vector Search) instead of a live loop.

## Next steps you could add

- Show image thumbnails in the results list (serve via `/uploads` static route)
- Pagination on `GET /api/images` once the dataset grows
- Vector index for faster comparison at scale
- User accounts / auth if this needs to be multi-user with permissions
