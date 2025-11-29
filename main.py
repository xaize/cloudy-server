from flask import Flask, jsonify, request
from flask_cors import CORS
import time
import os

app = Flask(__name__)
CORS(app)

latest_drop = {
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
        "service": "Cloudy Drop Server"
    })

@app.route('/latest', methods=['GET'])
def get_latest():
    global latest_drop
    
    if latest_drop["timestamp"] > 0 and (time.time() - latest_drop["timestamp"]) > 10:
        latest_drop = {"job": "", "name": "", "ms": 0.0, "players": "", "timestamp": 0}
    
    return jsonify({
        "job": latest_drop.get("job", ""),
        "name": latest_drop.get("name", ""),
        "ms": latest_drop.get("ms", 0.0),
        "players": latest_drop.get("players", ""),
    })

@app.route('/update', methods=['POST'])
def update_drop():
    global latest_drop
    
    try:
        data = request.get_json()
        
        if not data or 'job' not in data or 'name' not in data or 'ms' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        latest_drop = {
            'job': str(data['job']),
            'name': str(data['name']),
            'ms': float(data['ms']),
            'players': str(data.get('players', '')),
            'timestamp': time.time()
        }
        
        print(f"✓ Drop: {data['name']} - ${data['ms']}M/s - Job: {data['job']}")
        
        return jsonify({"success": True, "data": latest_drop})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    age_seconds = time.time() - latest_drop.get("timestamp", 0) if latest_drop.get("timestamp", 0) > 0 else 0
    
    return jsonify({
        "status": "online",
        "current_drop": latest_drop,
        "age_seconds": age_seconds,
        "has_active_drop": latest_drop.get("job", "") != "" and age_seconds < 10
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
