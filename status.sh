#!/bin/bash
# Check bot status

if [ -f /var/run/mattermost-bot.pid ]; then
    PID=$(cat /var/run/mattermost-bot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Bot is running (PID: $PID)"
        echo ""
        echo "📊 Recent logs:"
        tail -10 /var/log/mattermost-bot/bot.log 2>/dev/null
    else
        echo "❌ Bot is not running (stale PID file)"
        rm /var/run/mattermost-bot.pid
    fi
else
    echo "❌ Bot is not running (no PID file)"
fi
