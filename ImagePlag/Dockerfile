# Single container running EVERYTHING: Python AI service, Express API, and
# the built React app -- one deployment, one URL, hosted on Hugging Face
# Spaces (which requires the container to listen on port 7860).
#
# Layout inside the container:
#   Python service -> runs internally on localhost:8000, never exposed
#   Express server -> the ONLY public process, listens on port 7860,
#                      serves the API AND the built React app (server/public)

FROM node:20-bookworm

# --- System-level Python (for the AI service) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Python service setup ---
COPY python-service/requirements.txt ./python-service/requirements.txt
RUN python3 -m venv /app/python-service/venv \
    && /app/python-service/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /app/python-service/venv/bin/pip install --no-cache-dir -r ./python-service/requirements.txt
COPY python-service/ ./python-service/

# --- Client build (React -> static files) ---
COPY client/package*.json ./client/
RUN cd client && npm install
COPY client/ ./client/
RUN cd client && npm run build

# --- Node server setup ---
COPY server/package*.json ./server/
RUN cd server && npm install --omit=dev
COPY server/ ./server/
RUN mkdir -p ./server/uploads

# Drop the built React app where server.js already looks for it
RUN mkdir -p ./server/public && cp -r ./client/dist/. ./server/public/

COPY start.sh ./start.sh
RUN chmod +x ./start.sh

# Hugging Face Spaces requires the container to listen on 7860 specifically
ENV PORT=7860
ENV PYTHON_SERVICE_URL=http://localhost:8000
EXPOSE 7860

CMD ["./start.sh"]
