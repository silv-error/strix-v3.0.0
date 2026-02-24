# Discord Auto-Kick Bot v3.0

Professional Discord bot that automatically kicks members who don't verify within a set time period.

## 📁 File Structure

```
autokick_bot/
│
├── main.py                 # Entry point - Run this file
├── bot.py                  # Bot class and core functionality
├── config.py               # Configuration settings
├── tasks.py                # Background tasks (auto-kick checker)
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
│
├── commands/              # All bot commands
│   ├── __init__.py
│   ├── slash_commands.py  # Modern slash commands (/)
│   └── prefix_commands.py # Legacy prefix commands (!)
│
├── events/                # Discord event handlers
│   ├── __init__.py
│   └── member_events.py   # Member join/update/remove events
│
└── utils/                 # Utility functions
    ├── __init__.py
    ├── data_manager.py    # Data loading and saving
    └── logger.py          # Kick logging to channels
```

## 🎯 File Purposes

### Core Files

- **`main.py`** - Program entry point. Run this to start the bot.
- **`bot.py`** - Bot class definition and initialization.
- **`config.py`** - All configuration variables in one place.
- **`tasks.py`** - Background tasks that check for expired members.

### Commands (`commands/`)

- **`slash_commands.py`** - Modern slash commands (`/setup`, `/status`, etc.)
- **`prefix_commands.py`** - Legacy prefix commands (`!setup`, etc.)

### Events (`events/`)

- **`member_events.py`** - Handles member join, role updates, and leaves

### Utils (`utils/`)

- **`data_manager.py`** - Loads and saves JSON data files
- **`logger.py`** - Sends professional kick logs to Discord channels

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your bot token
```

### 3. Run the Bot

```bash
python main.py
```

Or with token as argument:
```bash
python main.py YOUR_BOT_TOKEN
```

## ⚙️ Configuration

Edit `config.py` to change default settings:

```python
UNVERIFIED_ROLE_NAME = "Unverified"
KICK_AFTER_MINUTES = 30
CHECK_INTERVAL_MINUTES = 1
SEND_DM_BEFORE_KICK = False
```

## 📋 Available Commands

### Slash Commands (Recommended)

- `/setup` - Configure role and kick timer
- `/status` - View tracked members
- `/setlogchannel` - Set where kick logs go
- `/toggledm` - Enable/disable DM notifications
- `/help` - Show all commands

### Prefix Commands (Legacy)

- `!setup` - Configure settings
- `!autokick_help` - Show help

## 🔧 Customization

### Change Check Interval

Edit `config.py`:
```python
CHECK_INTERVAL_MINUTES = 5  # Check every 5 minutes
```

### Change Embed Colors

Edit `config.py`:
```python
COLOR_INFO = 0x3498db      # Blue
COLOR_SUCCESS = 0x2ecc71   # Green
COLOR_WARNING = 0xf39c12   # Orange
COLOR_ERROR = 0xe74c3c     # Red
```

### Modify Kick Log Format

Edit `utils/logger.py` to customize the log embed appearance.

### Add New Commands

1. For slash commands: Edit `commands/slash_commands.py`
2. For prefix commands: Edit `commands/prefix_commands.py`

## 📝 Data Files

The bot creates these files automatically:

- `unverified_members.json` - Tracks which members are unverified
- `guild_configs.json` - Stores per-server settings

**Don't delete these while the bot is running!**

## 🛠️ Development

### Project Structure Benefits

✅ **Organized** - Easy to find specific functionality  
✅ **Modular** - Each file has a single responsibility  
✅ **Maintainable** - Easy to update and extend  
✅ **Clean** - No 1000-line files  

### Adding New Features

1. **New command?** → Add to `commands/`
2. **New event?** → Add to `events/`
3. **New utility?** → Add to `utils/`
4. **New setting?** → Add to `config.py`

### Testing

```bash
# Set short intervals for testing
# Edit config.py:
CHECK_INTERVAL_MINUTES = 1
KICK_AFTER_MINUTES = 1

# Then run:
python main.py
```

## 📖 Documentation

- Full guide: See `GUIDE_V3.md`
- Configuration: See `config.py`
- Each file has detailed docstrings

## 🔐 Security

- ✅ Token stored in `.env` (not in code)
- ✅ `.gitignore` prevents committing secrets
- ✅ Environment variables supported

## 🆘 Troubleshooting

### Import Errors

Make sure you're in the correct directory:
```bash
cd autokick_bot/
python main.py
```

### Module Not Found

Install dependencies:
```bash
pip install -r requirements.txt
```

### Bot Won't Start

1. Check token in `.env` file
2. Verify all files are present
3. Check console for error messages

## 📦 Deployment

### Development

```bash
python main.py
```

### Production (Linux with screen)

```bash
screen -S autokick
python main.py
# Press Ctrl+A then D to detach
```

### Production (systemd)

Create `/etc/systemd/system/autokick-bot.service`:

```ini
[Unit]
Description=Discord Auto-Kick Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/autokick_bot
EnvironmentFile=/path/to/autokick_bot/.env
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable autokick-bot
sudo systemctl start autokick-bot
```

## 🤝 Contributing

This is a clean, organized structure that makes it easy to:
- Add new features
- Fix bugs
- Understand code flow
- Maintain the project

## 📄 License

MIT License - Feel free to use and modify!

---

**Built with ❤️ for Discord automation**

**Version:** 3.0  
**Python:** 3.8+  
**Discord.py:** 2.3.0+
