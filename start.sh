#!/bin/bash
# Mattermost Bot Startup Script

cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -q -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Copy .env.example to .env and fill in your credentials:"
    echo "   cp .env.example .env"
    echo ""
    echo "   Or set environment variables manually:"
    echo "   export MATTERMOST_TOKEN=your_token"
    echo "   export AGENT_ZERO_API_KEY=your_key"
    echo ""
fi

# Run the bot
echo "Starting Mattermost Bot..."
exec python bot.py
