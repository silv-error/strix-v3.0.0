"""
Legacy prefix commands for backward compatibility
"""
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from src.config import COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING, CHECK_INTERVAL_MINUTES
from src.utils import has_permission, get_permission_error_message


def register_prefix_commands(bot):
    """Register all prefix commands"""
    
    @bot.command(name='setup')
    async def setup_autokick(ctx, role_name: str = None, kick_after_minutes: int = None):
        """Configure auto-kick settings"""
        # Check permissions
        if not has_permission(bot, ctx):
            await ctx.send(get_permission_error_message(bot, ctx.guild.id))
            return
        
        guild_id = ctx.guild.id
        config = bot.get_guild_config(guild_id)
        
        # Show current config
        if role_name is None and kick_after_minutes is None:
            embed = discord.Embed(
                title="⚙️ Auto-Kick Configuration",
                description=f"Current settings for **{ctx.guild.name}**\n\n💡 **Tip:** Use `/setup` for slash commands!",
                color=COLOR_INFO
            )
            embed.add_field(name="Target Role", value=f"`{config['role_name']}`", inline=False)
            embed.add_field(name="Kick After", value=f"`{config['kick_after_minutes']}` minutes", inline=False)
            
            dm_status = "✅ Enabled" if config.get('send_dm', False) else "❌ Disabled"
            embed.add_field(name="DM Notifications", value=dm_status, inline=False)
            
            log_channel = ctx.guild.get_channel(config.get('log_channel_id')) if config.get('log_channel_id') else None
            log_status = log_channel.mention if log_channel else "❌ Not set"
            embed.add_field(name="Log Channel", value=log_status, inline=False)
            
            allowed_roles = config.get('allowed_roles', [])
            if allowed_roles:
                roles_text = "\n".join([f"• `{role}`" for role in allowed_roles])
                embed.add_field(name="Staff Roles", value=roles_text, inline=False)
            else:
                embed.add_field(name="Staff Roles", value="❌ None (Admin only)", inline=False)
            
            tracked_count = len(bot.unverified_members.get(guild_id, {}))
            embed.add_field(name="Currently Tracking", value=f"{tracked_count} member(s)", inline=False)
            
            await ctx.send(embed=embed)
            return
        
        # Update config
        if role_name is not None:
            config['role_name'] = role_name
        
        if kick_after_minutes is not None:
            if kick_after_minutes < 1:
                await ctx.send("❌ Kick time must be at least 1 minute.")
                return
            config['kick_after_minutes'] = kick_after_minutes
        
        bot.guild_configs[guild_id] = config
        bot.save_data()
        
        await ctx.send(f"✅ Configuration updated! Role: `{config['role_name']}`, Kick after: `{config['kick_after_minutes']}` minutes")
        
        bot.unverified_members[guild_id] = {}
        from src.tasks import scan_existing_members
        await scan_existing_members(bot)
    
    @bot.command(name='status')
    async def status_command(ctx):
        """View tracked members"""
        # Check permissions
        if not has_permission(bot, ctx):
            await ctx.send(get_permission_error_message(bot, ctx.guild.id))
            return
        
        guild_id = ctx.guild.id
        config = bot.get_guild_config(guild_id)
        
        if guild_id not in bot.unverified_members or not bot.unverified_members[guild_id]:
            await ctx.send("✅ No unverified members currently being tracked.")
            return
        
        embed = discord.Embed(
            title="📊 Auto-Kick Status",
            description=f"Members with `{config['role_name']}` role",
            color=COLOR_WARNING
        )
        
        now = datetime.now()
        kick_threshold = timedelta(minutes=config['kick_after_minutes'])
        
        tracked_count = 0
        for member_id, join_timestamp in bot.unverified_members[guild_id].items():
            member = ctx.guild.get_member(member_id)
            
            if member:
                join_time = datetime.fromtimestamp(join_timestamp)
                time_elapsed = now - join_time
                time_remaining = kick_threshold - time_elapsed
                
                if time_remaining.total_seconds() > 0:
                    minutes_remaining = int(time_remaining.total_seconds() / 60)
                    seconds_remaining = int(time_remaining.total_seconds() % 60)
                    embed.add_field(
                        name=f"{member.name}",
                        value=f"⏱️ {minutes_remaining}m {seconds_remaining}s",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name=f"{member.name}",
                        value=f"⚠️ Overdue",
                        inline=True
                    )
                
                tracked_count += 1
                if tracked_count >= 25:
                    break
        
        embed.set_footer(text=f"Total: {len(bot.unverified_members[guild_id])} | Next check in ~{CHECK_INTERVAL_MINUTES} min")
        await ctx.send(embed=embed)
    
    @bot.command(name='setlogchannel')
    async def set_log_channel(ctx, channel: discord.TextChannel):
        """Set the log channel"""
        # Check permissions
        if not has_permission(bot, ctx):
            await ctx.send(get_permission_error_message(bot, ctx.guild.id))
            return
        
        guild_id = ctx.guild.id
        config = bot.get_guild_config(guild_id)
        
        config['log_channel_id'] = channel.id
        bot.guild_configs[guild_id] = config
        bot.save_data()
        
        await ctx.send(f"✅ Log channel set to {channel.mention}")
        
        # Send test message
        test_embed = discord.Embed(
            description="✅ **Log channel configured successfully**\nKick logs will appear here.",
            color=COLOR_SUCCESS,
            timestamp=datetime.now()
        )
        test_embed.set_footer(text="Auto-Kick System")
        
        try:
            await channel.send(embed=test_embed)
        except:
            await ctx.send("⚠️ Make sure I have permissions to send messages in that channel!")
    
    @bot.command(name='toggledm')
    async def toggle_dm(ctx, enabled: str):
        """Toggle DM notifications (on/off)"""
        # Check permissions
        if not has_permission(bot, ctx):
            await ctx.send(get_permission_error_message(bot, ctx.guild.id))
            return
        
        guild_id = ctx.guild.id
        config = bot.get_guild_config(guild_id)
        
        if enabled.lower() in ['on', 'enable', 'enabled', 'yes', 'true']:
            config['send_dm'] = True
            status = "enabled ✅"
        elif enabled.lower() in ['off', 'disable', 'disabled', 'no', 'false']:
            config['send_dm'] = False
            status = "disabled ❌"
        else:
            await ctx.send("❌ Invalid option. Use `on` or `off`")
            return
        
        bot.guild_configs[guild_id] = config
        bot.save_data()
        
        await ctx.send(f"📬 DM notifications are now **{status}**")
    
    @bot.command(name='addrole')
    async def add_role(ctx, role: discord.Role):
        """Add staff role permissions"""
        # Only admins can add roles
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Only Administrators can add staff roles.")
            return
        
        guild_id = ctx.guild.id
        config = bot.get_guild_config(guild_id)
        
        allowed_roles = config.get('allowed_roles', [])
        
        if role.name in allowed_roles:
            await ctx.send(f"⚠️ Role {role.mention} already has bot permissions!")
            return
        
        allowed_roles.append(role.name)
        config['allowed_roles'] = allowed_roles
        bot.guild_configs[guild_id] = config
        bot.save_data()
        
        await ctx.send(f"✅ {role.mention} can now use bot commands!")
    
    @bot.command(name='removerole')
    async def remove_role(ctx, role: discord.Role):
        """Remove staff role permissions"""
        # Only admins can remove roles
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Only Administrators can remove staff roles.")
            return
        
        guild_id = ctx.guild.id
        config = bot.get_guild_config(guild_id)
        
        allowed_roles = config.get('allowed_roles', [])
        
        if role.name not in allowed_roles:
            await ctx.send(f"⚠️ Role {role.mention} doesn't have bot permissions!")
            return
        
        allowed_roles.remove(role.name)
        config['allowed_roles'] = allowed_roles
        bot.guild_configs[guild_id] = config
        bot.save_data()
        
        await ctx.send(f"✅ {role.mention} can no longer use bot commands!")
    
    @bot.command(name='listroles')
    async def list_roles(ctx):
        """List staff roles"""
        # Check permissions
        if not has_permission(bot, ctx):
            await ctx.send(get_permission_error_message(bot, ctx.guild.id))
            return
        
        guild_id = ctx.guild.id
        config = bot.get_guild_config(guild_id)
        
        allowed_roles = config.get('allowed_roles', [])
        
        embed = discord.Embed(
            title="👥 Staff Roles with Bot Permissions",
            color=COLOR_INFO
        )
        
        if allowed_roles:
            roles_list = "\n".join([f"• `{role}`" for role in allowed_roles])
            embed.add_field(name="Staff Roles", value=roles_list, inline=False)
        else:
            embed.add_field(name="Staff Roles", value="❌ None (Admin only)", inline=False)
        
        embed.add_field(
            name="💡 How to Add",
            value="Use `!addrole @YourStaffRole`",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @bot.command(name='help')
    async def help_command(ctx):
        """Show help message"""
        embed = discord.Embed(
            title="🤖 Auto-Kick Bot Commands",
            description="💡 **Tip:** Use slash commands by typing `/` for a better experience!",
            color=COLOR_INFO
        )
        
        embed.add_field(
            name="📋 Basic Commands",
            value="`!setup` or `/setup` - Configure settings\n"
                  "`!status` or `/status` - View tracked members\n"
                  "`!help` or `/help` - Show this message",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Configuration",
            value="`!setlogchannel #channel` - Set log channel\n"
                  "`!toggledm on/off` - Toggle DM notifications",
            inline=False
        )
        
        embed.add_field(
            name="👥 Staff Management",
            value="`!addrole @role` - Give role bot permissions\n"
                  "`!removerole @role` - Remove permissions\n"
                  "`!listroles` - List staff roles",
            inline=False
        )
        
        # Check permissions
        if has_permission(bot, ctx):
            embed.set_footer(text="✅ You have permission to use these commands")
        else:
            embed.set_footer(text="⚠️ You don't have permission to use these commands")
        
        await ctx.send(embed=embed)
    
    @bot.event
    async def on_command_error(ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need Administrator permissions to use this command.")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Member not found.")
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send("❌ Role not found.")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ Channel not found.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument. Use `!help` to see command usage.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument. Use `!help` to see command usage.")
