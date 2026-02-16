#!/bin/bash
# Stop the bot

if [ -f /var/run/mattermost-bot.pid ]; then
    PID=$(cat /var/run/mattermost-bot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping bot (PID: $PID)..."
        kill $PID
        sleep 2
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force killing..."
            kill -9 $PID
        fi
        rm /var/run/mattermost-bot.pid
        echo "✅ Bot stopped"
    else
        echo "Bot not running (stale PID file)"
        rm /var/run/mattermost-bot.pid
    fi
else
    echo "Bot not running (no PID file)"
fi
