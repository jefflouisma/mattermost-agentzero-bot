# Mattermost Bot for Agent Zero

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Production-grade bot service that connects [Mattermost](https://mattermost.com/) to [Agent Zero](https://github.com/frdel/agent-zero) AI assistant via WebSocket.

## 🌟 Features

- ✅ **WebSocket connection** - Real-time message reception (no polling needed)
- ✅ **DM support** - Works in direct messages (unlike outgoing webhooks)
- ✅ **Conversation memory** - Context per channel via Agent Zero's `context_id`
- ✅ **Auto-reconnect** - Exponential backoff on connection failure
- ✅ **Graceful shutdown** - Handles SIGTERM/SIGINT properly
- ✅ **Secure credential handling** - Environment variables / `.env` file
- ✅ **Multiple deployment options** - Direct, systemd, Supervisor, or Docker
- ✅ **Comprehensive logging** - Structured logging with multiple levels
- ✅ **Error handling** - Robust error handling for all external calls

---

## 🏗️ Architecture

```
┌─────────────┐     WebSocket      ┌─────────┐     HTTP API     ┌─────────────┐
│ Mattermost  │ ←───────────────→ │   Bot   │ ←──────────────→ │ Agent Zero  │
│  Server     │   (receives msgs)  │ Service │  (AI requests)   │   AI API    │
└─────────────┘                    └─────────┘                  └─────────────┘
```

**Key advantage**: Uses WebSocket (outbound connection) instead of webhooks:
- No exposed HTTP endpoint needed
- Works in DMs and private channels
- No firewall/NAT configuration required

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/jefflouisma/mattermost-agentzero-bot.git
cd mattermost-agentzero-bot
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your actual credentials
nano .env  # or vim, or any editor
```

**Required variables:**

| Variable | Description | Where to get |
|----------|-------------|--------------|
| `MATTERMOST_TOKEN` | Bot account token | Mattermost System Console → Integrations → Bot Accounts |
| `AGENT_ZERO_API_KEY` | API key for Agent Zero | Agent Zero Settings → External Services |

**Optional variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `MATTERMOST_URL` | `mattermost.house.svc.cluster.local` | Mattermost server hostname |
| `MATTERMOST_PORT` | `8065` | Mattermost server port |
| `MATTERMOST_SCHEME` | `http` | `http` or `https` |
| `AGENT_ZERO_URL` | `http://agent-zero.house.svc.cluster.local` | Agent Zero API URL |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

## 🚀 Usage

### Quick Start (Direct Run)

```bash
./start.sh
```

### Management Commands

| Command | Description |
|---------|-------------|
| `./start.sh` | Start the bot |
| `./stop.sh` | Stop the bot |
| `./restart.sh` | Restart the bot |
| `./status.sh` | Check bot status |
| `./logs.sh` | View live logs (Ctrl+C to exit) |

### Testing

1. **Direct Message**: Open a DM with `@agentzero` in Mattermost and type `Hello!`
2. **Channel Mention**: Invite `@agentzero` to a channel and mention it

The bot will forward messages to Agent Zero and reply with the AI response.

---

## 🔒 Security

### Credential Handling

**⚠️ IMPORTANT**: Never commit credentials to version control!

This project uses environment variables for all sensitive configuration:

1. **Development**: Use `.env` file (automatically loaded via `python-dotenv`)
2. **Production**: Use actual environment variables or secrets management

The `.env` file is excluded from git via `.gitignore`.

### Service Configuration Files

The repository includes template service files:

- `mattermost-bot.service` - systemd service (with placeholders)
- `mattermost-bot.service.example` - Template for reference
- `supervisord.conf` - Supervisor config (with placeholders)
- `supervisord.conf.example` - Template for reference

**Before using in production**, copy these files and replace the placeholder values:
- `YOUR_MATTERMOST_TOKEN_HERE` → Your actual bot token
- `YOUR_AGENT_ZERO_API_KEY_HERE` → Your actual API key

### Best Practices

- ✅ `.env` file has `600` permissions (owner read/write only)
- ✅ `.env` is in `.gitignore` (never committed)
- ✅ `.env.example` shows required variables without real values
- ✅ Bot validates required variables on startup

---

## 🖥️ Deployment Options

### Option 1: systemd (Recommended for Linux)

1. Copy and configure the service file:
   ```bash
   sudo cp mattermost-bot.service /etc/systemd/system/
   sudo nano /etc/systemd/system/mattermost-bot.service
   # Replace YOUR_*_HERE placeholders with actual values
   ```

2. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable mattermost-bot
   sudo systemctl start mattermost-bot
   sudo systemctl status mattermost-bot
   ```

3. View logs:
   ```bash
   sudo journalctl -u mattermost-bot -f
   ```

### Option 2: Supervisor

1. Install and configure:
   ```bash
   sudo apt-get install supervisor
   sudo cp supervisord.conf /etc/supervisor/conf.d/mattermost-bot.conf
   sudo nano /etc/supervisor/conf.d/mattermost-bot.conf
   # Replace YOUR_*_HERE placeholders with actual values
   ```

2. Start:
   ```bash
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start mattermost-bot
   ```

3. View logs:
   ```bash
   sudo tail -f /var/log/mattermost-bot.out.log
   sudo tail -f /var/log/mattermost-bot.err.log
   ```

### Option 3: Docker

```bash
# Build
docker build -t mattermost-agentzero-bot .

# Run with environment variables
docker run -d \\
  --name mattermost-bot \\
  -e MATTERMOST_TOKEN=your_token \\
  -e AGENT_ZERO_API_KEY=your_key \\
  -e MATTERMOST_URL=mattermost.example.com \\
  mattermost-agentzero-bot
```

### Option 4: Docker Compose

```yaml
version: '3.8'

services:
  mattermost-bot:
    build: .
    container_name: mattermost-bot
    environment:
      - MATTERMOST_TOKEN=${MATTERMOST_TOKEN}
      - AGENT_ZERO_API_KEY=${AGENT_ZERO_API_KEY}
      - MATTERMOST_URL=mattermost.example.com
      - MATTERMOST_SCHEME=https
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 📁 Project Structure

```
.
├── bot.py                          # Main bot service
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template (safe to commit)
├── .gitignore                      # Excludes .env and sensitive files
├── README.md                       # This file
├── start.sh                        # Start script
├── stop.sh                         # Stop script
├── status.sh                       # Status check
├── restart.sh                      # Restart script
├── logs.sh                         # Log viewer
├── mattermost-bot.service          # systemd service (placeholders)
├── mattermost-bot.service.example  # systemd template
├── supervisord.conf                # Supervisor config (placeholders)
└── supervisord.conf.example        # Supervisor template
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Missing required environment variables" | Create `.env` file from `.env.example` |
| "Authentication failed" | Check `MATTERMOST_TOKEN` is valid |
| "Cannot connect to AI service" | Verify Agent Zero is running |
| Bot not responding to DMs | Ensure bot is added to the channel/DM |
| WebSocket disconnects | Check network; bot auto-reconnects |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- [Agent Zero](https://github.com/frdel/agent-zero) - The AI assistant framework
- [mattermostdriver](https://github.com/Vaelor/python-mattermost-driver) - Python Mattermost driver
- [Mattermost](https://mattermost.com/) - Open source collaboration platform
