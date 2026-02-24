"""
Permission checking utilities
"""
import discord
from discord.ext import commands


def has_permission(bot, interaction_or_ctx):
    """
    Check if user has permission to use bot commands
    
    Returns True if:
    - User is Administrator
    - User has one of the allowed staff roles
    """
    # Get member and guild
    if isinstance(interaction_or_ctx, discord.Interaction):
        member = interaction_or_ctx.user
        guild_id = interaction_or_ctx.guild.id
    else:  # Context from prefix command
        member = interaction_or_ctx.author
        guild_id = interaction_or_ctx.guild.id
    
    # Check if user is administrator
    if member.guild_permissions.administrator:
        return True
    
    # Check if user has any allowed staff roles
    config = bot.get_guild_config(guild_id)
    allowed_roles = config.get('allowed_roles', [])
    
    # Get user's role names
    user_role_names = [role.name for role in member.roles]
    
    # Check if user has any allowed role
    for role_name in allowed_roles:
        if role_name in user_role_names:
            return True
    
    return False


def get_permission_error_message(bot, guild_id):
    """Get error message for permission denied"""
    config = bot.get_guild_config(guild_id)
    allowed_roles = config.get('allowed_roles', [])
    
    if allowed_roles:
        roles_list = ", ".join([f"`{role}`" for role in allowed_roles])
        return f"❌ You need Administrator permission or one of these roles: {roles_list}"
    else:
        return "❌ You need Administrator permission to use this command."
