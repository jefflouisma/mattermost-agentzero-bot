#!/usr/bin/env python3
"""
Mattermost Bot for Agent Zero - Production Grade
Receives messages via WebSocket, forwards to Agent Zero External API

Security: All credentials must be provided via environment variables
or .env file (not committed to version control)
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Optional

import requests
from mattermostdriver import Driver

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Environment variables must be set manually

# ============ CONFIGURATION ============
# ALL values must be set via environment variables - NO defaults for secrets!

MATTERMOST_URL = os.getenv("MATTERMOST_URL", "mattermost.house.svc.cluster.local")
MATTERMOST_PORT = int(os.getenv("MATTERMOST_PORT", "8065"))
MATTERMOST_TOKEN = os.getenv("MATTERMOST_TOKEN")  # REQUIRED - no default
MATTERMOST_SCHEME = os.getenv("MATTERMOST_SCHEME", "http")

AGENT_ZERO_URL = os.getenv("AGENT_ZERO_URL", "http://agent-zero.house.svc.cluster.local")
AGENT_ZERO_API_KEY = os.getenv("AGENT_ZERO_API_KEY")  # REQUIRED - no default

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
RECONNECT_DELAY = int(os.getenv("RECONNECT_DELAY", "5"))
MAX_RECONNECT_DELAY = int(os.getenv("MAX_RECONNECT_DELAY", "300"))
# ========================================

# Validate required configuration
def validate_config():
    """Ensure all required environment variables are set."""
    missing = []

    if not MATTERMOST_TOKEN:
        missing.append("MATTERMOST_TOKEN")
    if not AGENT_ZERO_API_KEY:
        missing.append("AGENT_ZERO_API_KEY")

    if missing:
        print("❌ ERROR: Missing required environment variables:", file=sys.stderr)
        for var in missing:
            print(f"   - {var}", file=sys.stderr)
        print("\nSet them via:", file=sys.stderr)
        print("   1. Environment variables (export VAR=value)", file=sys.stderr)
        print("   2. .env file (copy .env.example to .env and fill in)", file=sys.stderr)
        print("\nSee README.md for setup instructions.", file=sys.stderr)
        sys.exit(1)

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Track conversation contexts per channel
contexts: dict[str, str] = {}
mm: Optional[Driver] = None
shutdown_requested = False


def get_agent_zero_response(message: str, context_id: Optional[str] = None) -> tuple[str, Optional[str]]:
    """Send message to Agent Zero External API and return response."""
    url = f"{AGENT_ZERO_URL}/api_message"
    headers = {"X-API-KEY": AGENT_ZERO_API_KEY}
    payload = {"message": message}

    if context_id:
        payload["context_id"] = context_id

    try:
        logger.debug(f"Sending to Agent Zero: {message[:100]}...")
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "No response"), data.get("context_id")
    except requests.exceptions.Timeout:
        logger.error("Agent Zero request timed out")
        return "Request timed out. Please try again.", None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Cannot connect to Agent Zero: {e}")
        return "Cannot connect to AI service. Please check if it's running.", None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Agent Zero HTTP error: {e}")
        return f"Error from AI service: {e.response.status_code}", None
    except Exception as e:
        logger.error(f"Unexpected error calling Agent Zero: {e}")
        return f"Error: {str(e)}", None


async def handle_event(event: str, driver: Driver):
    """Handle incoming Mattermost WebSocket events."""
    try:
        data = json.loads(event)
        event_type = data.get("event")

        # Only process new posts
        if event_type != "posted":
            return

        post_data = json.loads(data["data"]["post"])
        message = post_data.get("message", "").strip()
        channel_id = post_data.get("channel_id")
        user_id = post_data.get("user_id")
        sender_name = data["data"].get("sender_name", "unknown")

        # Skip empty messages
        if not message:
            return

        # Skip my own messages
        if user_id == driver.client.userid:
            return

        # Get or create context for this channel
        context_id = contexts.get(channel_id)

        logger.info(f"📩 [{sender_name}] {message[:80]}{'...' if len(message) > 80 else ''}")

        # Get response from Agent Zero
        response, new_context_id = get_agent_zero_response(message, context_id)

        # Save context for conversation continuity
        if new_context_id:
            contexts[channel_id] = new_context_id
            logger.debug(f"Context saved for channel {channel_id}: {new_context_id}")

        # Send response back to Mattermost
        try:
            driver.posts.create_post({
                "channel_id": channel_id,
                "message": response
            })
            logger.info(f"📤 Response sent: {response[:80]}{'...' if len(response) > 80 else ''}")
        except Exception as e:
            logger.error(f"Failed to send response to Mattermost: {e}")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse event JSON: {e}")
    except Exception as e:
        logger.error(f"Error handling event: {e}", exc_info=True)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down...")
    shutdown_requested = True
    if mm:
        try:
            mm.logout()
        except:
            pass
    sys.exit(0)


def connect_to_mattermost() -> Driver:
    """Establish connection to Mattermost."""
    logger.info(f"🔌 Connecting to Mattermost at {MATTERMOST_SCHEME}://{MATTERMOST_URL}:{MATTERMOST_PORT}...")

    driver = Driver({
        "url": MATTERMOST_URL,
        "token": MATTERMOST_TOKEN,
        "scheme": MATTERMOST_SCHEME,
        "port": MATTERMOST_PORT,
        "verify": False,  # Internal cluster, skip SSL verification
    })

    driver.login()
    bot_info = driver.users.get_user("me")
    logger.info(f"✅ Logged in as: {bot_info['username']} ({bot_info['id']})")

    return driver


def run_bot():
    """Main bot loop with reconnection logic."""
    global mm, shutdown_requested

    # Validate configuration before starting
    validate_config()

    reconnect_delay = RECONNECT_DELAY

    while not shutdown_requested:
        try:
            # Connect to Mattermost
            mm = connect_to_mattermost()

            # Reset reconnect delay on successful connection
            reconnect_delay = RECONNECT_DELAY

            logger.info("👂 Listening for messages via WebSocket...")
            logger.info("   • Bot responds to DMs")
            logger.info("   • Bot responds to mentions in channels it's in")
            logger.info("   • Press Ctrl+C to stop")

            # Start WebSocket listener (blocks until disconnect)
            mm.init_websocket(lambda e: handle_event(e, mm))

        except Exception as e:
            logger.error(f"Connection error: {e}")

        if shutdown_requested:
            break

        # Reconnect with exponential backoff
        logger.info(f"Reconnecting in {reconnect_delay} seconds...")
        time.sleep(reconnect_delay)
        reconnect_delay = min(reconnect_delay * 2, MAX_RECONNECT_DELAY)

    logger.info("👋 Bot shutdown complete")


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 50)
    logger.info("Mattermost Bot for Agent Zero - Starting")
    logger.info("=" * 50)

    # Log configuration (without sensitive data)
    logger.info(f"Mattermost: {MATTERMOST_SCHEME}://{MATTERMOST_URL}:{MATTERMOST_PORT}")
    logger.info(f"Agent Zero: {AGENT_ZERO_URL}")
    logger.info(f"Log Level: {LOG_LEVEL}")

    run_bot()
