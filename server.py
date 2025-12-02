"""
Cloudy Sniper - Server-Hosted Backend
Deploy this to Railway, Render, or Fly.io for global access
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import discord
from discord.ext import commands
import asyncio
import threading
import time
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from Roblox

# Global state
latest_drop = {
    "job": "",
    "name": "",
    "ms": 0.0,
    "players": "",
    "timestamp": 0
}

discord_client = None
bot_ready = False
connection_status = "disconnected"

# Configuration - Use environment variables for security
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')  # Set in hosting platform
DISCORD_CHANNEL_ID = 1401775181025775738


# === DISCORD BOT SETUP ===
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)


@discord_client.event
async def on_ready():
    global bot_ready, connection_status
    bot_ready = True
    connection_status = "connected"
    print(f'✅ Discord Bot Ready: {discord_client.user}')
    print(f'🌐 Server Running - Accessible from anywhere!')


@discord_client.event
async def on_message(message):
    global latest_drop
    
    # Only process messages from the specific channel
    if message.channel.id != DISCORD_CHANNEL_ID:
        return
    
    if not message.embeds:
        return
    
    embed = message.embeds[0]
    
    # Parse drop data
    name = None
    money_str = None
    players = None
    job_id = None
    
    for field in embed.fields:
        field_name = field.name.strip().lower().replace(' ', '')
        field_value = field.value.replace("**", "").strip()
        
        # First field is usually the name
        if embed.fields.index(field) == 0:
            name = field_value
        elif "moneypersec" in field_name or "money/s" in field_name:
            money_str = field_value.replace("$", "").replace(",", "").replace(" ", "")
        elif "players" in field_name:
            players = field_value
        elif "jobid" in field_name:
            job_id = field_value
    
    # Validate data
    if not all([name, money_str, job_id]):
        return
    
    # Parse money value
    import re
    match = re.search(r'[\d\.]+', money_str)
    if not match:
        return
    
    money_num = float(match.group())
    
    # Update global state
    latest_drop = {
        "job": job_id,
        "name": name,
        "ms": money_num,
        "players": players or "Unknown",
        "timestamp": time.time()
    }
    
    print(f'📦 NEW DROP: {name} | ${money_num:,.0f}M/s | {players}')


# === API ENDPOINTS ===
@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "online",
        "service": "Cloudy Sniper API",
        "version": "3.0",
        "discord_status": connection_status,
        "uptime": time.time()
    })


@app.route('/latest')
def get_latest_drop():
    """Get the latest job drop - called by Roblox scripts"""
    global latest_drop
    
    # Clear old drops (older than 10 seconds)
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
    """Get server status"""
    return jsonify({
        "discord_connected": bot_ready,
        "connection_status": connection_status,
        "active_drop": latest_drop["name"] != "",
        "server_time": datetime.now().isoformat()
    })


@app.route('/health')
def health_check():
    """Render.com health check endpoint"""
    return jsonify({"status": "healthy"}), 200


# === DISCORD BOT RUNNER ===
def run_discord_bot():
    """Run Discord bot in separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(discord_client.start(DISCORD_TOKEN))
    except Exception as e:
        print(f'❌ Discord Error: {e}')
        global connection_status
        connection_status = "error"


# === STARTUP ===
if __name__ == '__main__':
    # Validate token
    if not DISCORD_TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not set!")
        print("Set it as an environment variable in your hosting platform")
        exit(1)
    
    print('🚀 Starting Cloudy Sniper Server...')
    
    # Start Discord bot in background thread
    discord_thread = threading.Thread(target=run_discord_bot, daemon=True)
    discord_thread.start()
    
    # Get port from environment (for hosting platforms)
    port = int(os.getenv('PORT', 8080))
    
    # Start Flask server
    print(f'🌐 Starting API server on port {port}...')
    app.run(host='0.0.0.0', port=port, threaded=True)
