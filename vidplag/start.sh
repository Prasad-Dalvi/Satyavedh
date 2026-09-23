#!/usr/bin/env bash
# Start VidPlag (server + static client at /)
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate

pip install -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
fi

uvicorn server.main:app --host 0.0.0.0 --port 8001 --reload
