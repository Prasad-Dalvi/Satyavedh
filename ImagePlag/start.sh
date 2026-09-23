#!/bin/bash
set -e

# Start the Python AI service in the background, on the internal-only port 8000
cd /app/python-service
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Give it a moment to come up before Node starts sending it traffic
sleep 5

# Start the Node server in the FOREGROUND -- this is what keeps the
# container alive and serves the app on port 7860 (what HF Spaces routes
# public traffic to)
cd /app/server
node server.js
