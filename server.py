"""
Cloudy Sniper - Server-Hosted Backend (Selfbot Compatible)
Deploy this to Railway, Render, or Fly.io for global access
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import threading
import time
import os
from datetime import datetime
import re
import sys

# Import discord AFTER checking installation
try:
    import discord
    print(f"Discord library loaded: {discord.__version__}")
except ImportError as e:
    print(f"FATAL: Could not import discord: {e}")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# Global state
latest_drop = {
    "job": "",
    "name": "",
    "ms": 0.0,
    "players": "",
    "timestamp": 0
}

processed_jobs = set()  # Track processed job IDs to avoid duplicates
discord_client = None
bot_ready = False
connection_status = "disconnected"
discord_started = False

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')
DISCORD_CHANNEL_ID = 1401775181025775738

print(f"Token configured: {bool(DISCORD_TOKEN)}")

# === DISCORD CLIENT SETUP (Selfbot compatible) ===
discord_client = discord.Client()


@discord_client.event
async def on_ready():
    global bot_ready, connection_status
    bot_ready = True
    connection_status = "connected"
    print(f'✅ Discord Ready: {discord_client.user}')
    print(f'🌐 Server Running!')


@discord_client.event
async def on_message(message):
    global latest_drop
    
    if message.channel.id != DISCORD_CHANNEL_ID:
        return
    
    if not message.embeds:
        return
    
    embed = message.embeds[0]
    
    name = None
    money_str = None
    players = None
    job_id = None
    
    for field in embed.fields:
        field_name = field.name.strip().lower().replace(' ', '')
        field_value = field.value.replace("**", "").strip()
        
        if embed.fields.index(field) == 0:
            name = field_value
        elif "moneypersec" in field_name or "money/s" in field_name:
            money_str = field_value.replace("$", "").replace(",", "").replace(" ", "")
        elif "players" in field_name:
            players = field_value
        elif "jobid" in field_name:
            job_id = field_value
    
    if not all([name, money_str, job_id]):
        return
    
    # Check for duplicates
    if job_id in processed_jobs:
        return
    
    match = re.search(r'[\d\.]+', money_str)
    if not match:
        return
    
    money_num = float(match.group())
    
    # Add to processed set
    processed_jobs.add(job_id)
    
    # Limit set size to prevent memory issues (keep last 1000)
    if len(processed_jobs) > 1000:
        processed_jobs.pop()
    
    latest_drop = {
        "job": job_id,
        "name": name,
        "ms": money_num,
        "players": players or "Unknown",
        "timestamp": time.time()
    }
    
    print(f'📦 DROP: {name} | ${money_num:,.0f}M/s | {players}')


# === DISCORD BOT RUNNER ===
def run_discord_bot():
    """Run Discord bot in separate thread"""
    global connection_status
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print('🔑 Connecting to Discord...')
        loop.run_until_complete(discord_client.start(DISCORD_TOKEN))
    except Exception as e:
        print(f'❌ Discord Error: {e}')
        connection_status = f"error: {e}"


def start_discord_bot():
    """Initialize Discord bot on first request"""
    global discord_started
    
    if discord_started:
        return
    
    discord_started = True
    
    if not DISCORD_TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not set!")
        return
    
    print('🚀 Starting Cloudy Sniper...')
    
    discord_thread = threading.Thread(target=run_discord_bot, daemon=True)
    discord_thread.start()


# === API ENDPOINTS ===
@app.route('/')
def home():
    start_discord_bot()
    
    return jsonify({
        "status": "online",
        "service": "Cloudy Sniper API",
        "version": "3.1-selfbot",
        "discord_status": connection_status,
        "bot_ready": bot_ready,
        "uptime": time.time()
    })


@app.route('/latest')
def get_latest_drop():
    global latest_drop
    
    start_discord_bot()
    
    if latest_drop["timestamp"] > 0 and (time.time() - latest_drop["timestamp"]) > 10:
        latest_drop = {
            "job": "",
            "name": "",
            "ms": 0.0,
            "players": "",
            "timestamp": 0
        }
    
    return jsonify(latest_drop)


@app.route('/status')
def get_status():
    start_discord_bot()
    
    return jsonify({
        "discord_connected": bot_ready,
        "connection_status": connection_status,
        "active_drop": latest_drop["name"] != "",
        "server_time": datetime.now().isoformat()
    })


@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200


print('='*50)
print('CLOUDY SNIPER INITIALIZED')
print(f'Discord.py version: {discord.__version__}')
print('='*50)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)
