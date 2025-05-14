#!/bin/bash

# Go to the scoutjar-semantic project
cd ~/projects/scoutjar/scoutjar-semantic

# Activate the Python virtual environment
source venv/bin/activate

# Pull latest code
git fetch origin
git reset --hard origin/mvp0.1

# Show current branch and commit
echo "🛠 Branch: $(git rev-parse --abbrev-ref HEAD)"
echo "🔖 Commit: $(git rev-parse --short HEAD)"

# Install Python dependencies
pip install -r requirements.txt

# Stop any existing scoutjar-semantic process
pm2 delete scoutjar-semantic-mvp0.1 || true

# Kill any manual python3 process or leftovers on port 5002
echo "🔪 Killing any process using port 5002..."
kill -9 $(lsof -t -i :5002) || true

# Start the Flask app with pm2
pm2 start "gunicorn -b 0.0.0.0:5002 app:app --timeout 180 --workers 2" --name "scoutjar-semantic-mvp0.1" --time

# Save the pm2 process list
pm2 save
