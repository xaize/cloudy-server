#!/bin/bash
set -e

echo "🧹 Cleaning up old discord installations..."
pip uninstall discord.py discord discord.py-self -y 2>/dev/null || true

echo "📦 Installing dependencies..."
pip install Flask==3.0.0
pip install flask-cors==4.0.0
pip install gunicorn==21.2.0
pip install aiohttp==3.9.1

echo "🔧 Installing discord.py-self..."
pip install discord.py-self==2.0.1

echo "✅ Build complete!"
