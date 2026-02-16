# Mattermost Bot for Agent Zero

Production-grade bot service that connects Mattermost to Agent Zero AI assistant.

## Architecture

```
┌─────────────┐     WebSocket      ┌─────────┐     HTTP API     ┌─────────────┐
│ Mattermost  │ ←───────────────→ │   Bot   │ ←──────────────→ │ Agent Zero  │
│ :8065       │                   │ Service │                  │ :80         │
└─────────────┘                   └─────────┘                  └─────────────┘
```

## Files

| File | Description |
|------|-------------|
| `bot.py` | Main bot service with WebSocket listener |
| `start.sh` | Startup script with venv management |
| `requirements.txt` | Python dependencies |
| `mattermost-bot.service` | systemd service definition |
| `supervisord.conf` | Supervisor process manager config |

## Quick Start

### Option 1: Direct Run
```bash
cd /a0/usr/workdir/mattermost-bot
./start.sh
```

### Option 2: systemd (if available)
```bash
sudo cp mattermost-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mattermost-bot
sudo systemctl start mattermost-bot
sudo systemctl status mattermost-bot
```

### Option 3: Supervisor
```bash
sudo apt-get install supervisor
sudo cp supervisord.conf /etc/supervisor/conf.d/mattermost-bot.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start mattermost-bot
```

### Option 4: Docker
```bash
docker build -t mattermost-bot .
docker run -d --name mattermost-bot mattermost-bot
```

## Configuration

All configuration is via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MATTERMOST_URL` | mattermost.house.svc.cluster.local | Mattermost server hostname |
| `MATTERMOST_PORT` | 8065 | Mattermost server port |
| `MATTERMOST_TOKEN` | (set) | Bot account token |
| `MATTERMOST_SCHEME` | http | http or https |
| `AGENT_ZERO_URL` | http://agent-zero.house.svc.cluster.local | Agent Zero API URL |
| `AGENT_ZERO_API_KEY` | (set) | Agent Zero API key |
| `LOG_LEVEL` | INFO | DEBUG, INFO, WARNING, ERROR |

## Features

- ✅ WebSocket connection for real-time message reception
- ✅ Works in DMs and channels
- ✅ Conversation context per channel (session memory)
- ✅ Automatic reconnection with exponential backoff
- ✅ Graceful shutdown on SIGTERM/SIGINT
- ✅ Comprehensive logging
- ✅ Health check endpoint
- ✅ Error handling for all external calls

## Monitoring

Check logs:
```bash
# systemd
sudo journalctl -u mattermost-bot -f

# Supervisor
sudo tail -f /var/log/mattermost-bot.out.log

# Direct
./start.sh  # logs to stdout
```

## Testing

1. Send DM to the bot user in Mattermost
2. Or invite bot to a channel and mention it
3. Bot should respond via Agent Zero
