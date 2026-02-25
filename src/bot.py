"""
Main bot class and initialization
"""
import discord
from discord.ext import commands
from src.config import (
    BOT_PREFIX, 
    UNVERIFIED_ROLE_NAME, 
    KICK_AFTER_MINUTES,
    SEND_DM_BEFORE_KICK
)
from .utils import DataManager


class AutoKickBot(commands.Bot):
    """Main bot class for Auto-Kick functionality"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        intents.message_content = True
        
        super().__init__(command_prefix=BOT_PREFIX, intents=intents, help_command=None)
        
        # Store member join times: {guild_id: {member_id: join_timestamp}}
        self.unverified_members = {}
        
        # Store guild-specific configurations
        self.guild_configs = {}
        
        # Load data from files
        self.load_data()
    
    def load_data(self):
        """Load saved data from JSON files"""
        self.unverified_members = DataManager.load_tracked_members()
        self.guild_configs = DataManager.load_guild_configs()
        
        member_count = sum(len(m) for m in self.unverified_members.values())
        config_count = len(self.guild_configs)
        
        if member_count > 0:
            print(f"✅ Loaded {member_count} tracked member(s)")
        if config_count > 0:
            print(f"✅ Loaded configs for {config_count} server(s)")
    
    def save_data(self):
        """Save data to JSON files"""
        DataManager.save_data(self.unverified_members, self.guild_configs)
    
    def get_guild_config(self, guild_id):
        """Get configuration for a guild, returns defaults if not set"""
        if guild_id not in self.guild_configs:
            self.guild_configs[guild_id] = {
                'role_name': UNVERIFIED_ROLE_NAME,
                'kick_after_minutes': KICK_AFTER_MINUTES,
                'send_dm': SEND_DM_BEFORE_KICK,
                'log_channel_id': None,
                'allowed_roles': []  # Staff roles that can use bot commands
            }
            self.save_data()
        # Ensure allowed_roles exists for older configs
        if 'allowed_roles' not in self.guild_configs[guild_id]:
            self.guild_configs[guild_id]['allowed_roles'] = []
            self.save_data()
        return self.guild_configs[guild_id]
    
    async def setup_hook(self):
        """Called when the bot is starting up"""
        from src.tasks import setup_background_tasks
        
        # Start background tasks
        setup_background_tasks(self)
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} slash command(s)")
        except Exception as e:
            print(f"❌ Failed to sync slash commands: {e}")

    async def log_kick(self, guild, member, time_unverified_minutes):
        """Send a professional log message to the configured log channel"""
        config = self.get_guild_config(guild.id)
        log_channel_id = config.get('log_channel_id')
        
        if not log_channel_id:
            return  # No log channel configured
        
        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return  # Channel not found or deleted
        
        # Calculate time components
        hours = time_unverified_minutes // 60
        minutes = time_unverified_minutes % 60
        
        if hours > 0:
            time_str = f"{hours}h {minutes}m"
        else:
            time_str = f"{minutes}m"
        
        # Create clean, professional embed
        embed = discord.Embed(
            description=f"**{member.mention}** was removed for not verifying within {config['kick_after_minutes']} minutes.",
            color=0x2b2d31,  # Discord dark gray
            timestamp=discord.datetime.now()
        )
        
        embed.set_author(
            name=f"{member.name}",
            icon_url=member.display_avatar.url if member.display_avatar else None
        )
        
        embed.add_field(
            name="Duration Unverified",
            value=f"`{time_str}`",
            inline=True
        )
        
        embed.add_field(
            name="User ID",
            value=f"`{member.id}`",
            inline=True
        )
        
        embed.set_footer(text="Auto-Kick System")
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            print(f"  ⚠️ Missing permissions to send logs to channel {log_channel.name}")
        except Exception as e:
            print(f"  ⚠️ Error sending log: {e}")


def create_bot():
    """Factory function to create and configure the bot"""
    return AutoKickBot()
