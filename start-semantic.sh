#!/bin/bash

cd ~/projects/scoutjar/scoutjar-semantic

# 🐍 Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "🔧 Creating .venv virtual environment..."
  python3 -m venv .venv
fi

# 🟢 Activate virtual environment
source .venv/bin/activate

# 🌀 Pull latest code
git fetch origin
git reset --hard origin/mvp0.1

# 🏷 Show current Git branch and commit
echo "🛠 Branch: $(git rev-parse --abbrev-ref HEAD)"
echo "🔖 Commit: $(git rev-parse --short HEAD)"

# 📦 Install dependencies
pip install -r requirements.txt

# ❌ Stop existing PM2 process
pm2 delete scoutjar-semantic-mvp0.1 || true

# 🧼 Kill any process on port 5002
echo "🔪 Killing any process using port 5002..."
kill -9 $(lsof -t -i :5002) || true

# 🚀 Start app with Gunicorn from .venv
GUNICORN_PATH="./.venv/bin/gunicorn"
pm2 start "$GUNICORN_PATH -b 0.0.0.0:5002 app:app --timeout 180 --workers 2" \
  --name "scoutjar-semantic-mvp0.1" --time

# 💾 Save PM2 process list
pm2 save
