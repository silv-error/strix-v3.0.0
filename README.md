# Strix

Professional Discord bot that automatically kicks members who don't verify within a set time period.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Bot

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

Create `.env` file to store your discord bot token:

```
DISCORD_BOT_TOKEN=your-secret-token-here
```

## 📄 License

MIT License - Feel free to use and modify!

---

**Built with ❤️ for Discord automation**

**Version:** 3.0  
**Python:** 3.8+  
**Discord.py:** 2.3.0+
