"""
Configuration settings for the Auto-Kick Bot
"""

# Bot Configuration
BOT_PREFIX = '!'

# Default Server Settings
UNVERIFIED_ROLE_NAME = "Unverified"
KICK_AFTER_MINUTES = 2880
CHECK_INTERVAL_MINUTES = 1
SEND_DM_BEFORE_KICK = False

# Permission Settings
ALLOWED_ROLE_NAMES = []  # Staff roles that can use bot commands (empty = admin only)

# Data Files
MEMBERS_DATA_FILE = 'unverified_members.json'
GUILD_CONFIG_FILE = 'guild_configs.json'

# Embed Colors (Discord color codes)
COLOR_INFO = 0x3498db      # Blue
COLOR_SUCCESS = 0x2ecc71   # Green
COLOR_WARNING = 0xf39c12   # Orange
COLOR_ERROR = 0xe74c3c     # Red
COLOR_DARK = 0x2b2d31      # Discord dark gray
