"""
Logging utilities for sending kick logs to Discord channels
"""
import discord
from datetime import datetime
from src.config import COLOR_DARK


async def send_kick_log(guild, member, time_unverified_minutes, log_channel_id, kick_after_minutes):
    """
    Send a professional log message to the configured log channel
    
    Args:
        guild: Discord guild object
        member: Discord member object who was kicked
        time_unverified_minutes: How long they were unverified (in minutes)
        log_channel_id: Channel ID where to send the log
        kick_after_minutes: Configured kick threshold
    """
    if not log_channel_id:
        return False
    
    log_channel = guild.get_channel(log_channel_id)
    if not log_channel:
        return False
    
    # Calculate time components
    hours = time_unverified_minutes // 60
    minutes = time_unverified_minutes % 60
    
    if hours > 0:
        time_str = f"{hours}h {minutes}m"
    else:
        time_str = f"{minutes}m"
    
    # Create clean, professional embed
    embed = discord.Embed(
        description=f"**{member.mention}** was removed for not verifying within {kick_after_minutes} minutes.",
        color=COLOR_DARK,
        timestamp=datetime.now()
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
        return True
    except discord.Forbidden:
        print(f"  ⚠️ Missing permissions to send logs to channel {log_channel.name}")
        return False
    except Exception as e:
        print(f"  ⚠️ Error sending log: {e}")
        return False
