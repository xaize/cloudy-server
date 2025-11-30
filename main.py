from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import time
import os

app = Flask(__name__)
CORS(app)

# Upstash Redis connection (falls back to in-memory if not configured)
REDIS_URL = os.environ.get('REDIS_URL', '')

def get_redis():
    """Get Redis client (or None if not configured)"""
    if not REDIS_URL:
        return None
    try:
        from upstash_redis import Redis
        return Redis.from_env()
    except:
        return None

# Fallback in-memory storage
memory_storage = {
    "job": "",
    "name": "",
    "ms": 0.0,
    "players": "",
    "timestamp": 0
}

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Cloudy Server (Global Edge)",
        "version": "3.0-edge",
        "storage": "redis" if get_redis() else "memory",
        "region": os.environ.get('VERCEL_REGION', 'unknown')
    })

@app.route('/update', methods=['POST'])
def update():
    try:
        data = request.json
        drop_data = {
            "job": data.get("job", ""),
            "name": data.get("name", ""),
            "ms": float(data.get("ms", 0.0)),
            "players": data.get("players", ""),
            "timestamp": time.time()
        }
        
        # Try Redis first, fallback to memory
        redis = get_redis()
        if redis:
            redis.set('latest_drop', json.dumps(drop_data))
        else:
            global memory_storage
            memory_storage = drop_data
        
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/latest', methods=['GET'])
def get_latest():
    try:
        # Try Redis first
        redis = get_redis()
        if redis:
            data = redis.get('latest_drop')
            if data:
                return jsonify(json.loads(data))
        
        # Fallback to memory
        return jsonify(memory_storage)
    except Exception as e:
        return jsonify(memory_storage)

@app.route('/ping', methods=['GET'])
def ping():
    """Quick ping endpoint for latency testing"""
    return jsonify({
        "pong": True,
        "timestamp": time.time()
    })

# Vercel serverless handler
app = app
