"""
Discord member event handlers
"""
import discord
from discord.ext import commands
import asyncio
from datetime import datetime


def setup_member_events(bot):
    """Register member event handlers"""
    
    @bot.event
    async def on_member_update(before: discord.Member, after: discord.Member):
        """Track when a member gets or loses the unverified role"""
        guild_id = after.guild.id
        config = bot.get_guild_config(guild_id)
        
        unverified_role = discord.utils.get(after.guild.roles, name=config['role_name'])
        
        if not unverified_role:
            return
        
        member_id = after.id
        
        if guild_id not in bot.unverified_members:
            bot.unverified_members[guild_id] = {}
        
        # Member just got the unverified role
        if unverified_role not in before.roles and unverified_role in after.roles:
            bot.unverified_members[guild_id][member_id] = datetime.now().timestamp()
            bot.save_data()
            print(f"[{after.guild.name}] ▶️ Started tracking {after.name}")
        
        # Member lost the unverified role (verified!)
        elif unverified_role in before.roles and unverified_role not in after.roles:
            if member_id in bot.unverified_members.get(guild_id, {}):
                del bot.unverified_members[guild_id][member_id]
                bot.save_data()
                print(f"[{after.guild.name}] ⏹️ Stopped tracking {after.name} (verified)")
    
    @bot.event
    async def on_member_join(member: discord.Member):
        """Track new members if they get the unverified role immediately"""
        await asyncio.sleep(2)  # Small delay to let roles be assigned
        
        guild_id = member.guild.id
        config = bot.get_guild_config(guild_id)
        
        unverified_role = discord.utils.get(member.guild.roles, name=config['role_name'])
        
        if unverified_role and unverified_role in member.roles:
            if guild_id not in bot.unverified_members:
                bot.unverified_members[guild_id] = {}
            
            bot.unverified_members[guild_id][member.id] = datetime.now().timestamp()
            bot.save_data()
            print(f"[{member.guild.name}] 👋 New member {member.name} joined with unverified role")
    
    @bot.event
    async def on_member_remove(member: discord.Member):
        """Clean up data when a member leaves"""
        guild_id = member.guild.id
        member_id = member.id
        
        if guild_id in bot.unverified_members and member_id in bot.unverified_members[guild_id]:
            del bot.unverified_members[guild_id][member_id]
            bot.save_data()
