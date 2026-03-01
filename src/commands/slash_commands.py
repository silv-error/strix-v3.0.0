
import discord
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
from src.config import COLOR_INFO, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING
from src.utils import has_permission, get_permission_error_message


def register_slash_commands(bot):
    """Register all slash commands"""
    
    @bot.tree.command(name="setup", description="Configure auto-kick settings for this server")
    @app_commands.describe(
        role="The unverified role to track (mention it)",
        kick_after_minutes="Minutes before kicking (minimum 1)"
    )
    async def slash_setup(
        interaction: discord.Interaction,
        role: Optional[discord.Role] = None,
        kick_after_minutes: Optional[int] = None
    ):
        """Slash command for setup"""
        # Check permissions
        if not has_permission(bot, interaction):
            await interaction.response.send_message(
                get_permission_error_message(bot, interaction.guild.id),
                ephemeral=True
            )
            return
        
        guild_id = interaction.guild.id
        config = bot.get_guild_config(guild_id)
        
        # If no parameters, show current config
        if role is None and kick_after_minutes is None:
            embed = discord.Embed(
                title="⚙️ Auto-Kick Configuration",
                description=f"Current settings for **{interaction.guild.name}**",
                color=COLOR_INFO
            )
            
            # Show current role with mention if it exists
            current_role = discord.utils.get(interaction.guild.roles, name=config['role_name'])
            if current_role:
                embed.add_field(name="Target Role", value=f"{current_role.mention} (`{config['role_name']}`)", inline=False)
            else:
                embed.add_field(name="Target Role", value=f"`{config['role_name']}` ⚠️ (Role not found)", inline=False)
            
            embed.add_field(name="Kick After", value=f"`{config['kick_after_minutes']}` minutes", inline=False)
            
            dm_status = "✅ Enabled" if config.get('send_dm', False) else "❌ Disabled"
            embed.add_field(name="DM Notifications", value=dm_status, inline=False)
            
            log_channel = interaction.guild.get_channel(config.get('log_channel_id')) if config.get('log_channel_id') else None
            log_status = log_channel.mention if log_channel else "❌ Not set"
            embed.add_field(name="Log Channel", value=log_status, inline=False)
            
            # Show allowed roles
            allowed_roles = config.get('allowed_roles', [])
            if allowed_roles:
                roles_text = "\n".join([f"• `{role}`" for role in allowed_roles])
                embed.add_field(name="Staff Roles (Can Use Bot)", value=roles_text, inline=False)
            else:
                embed.add_field(name="Staff Roles", value="❌ None (Admin only)", inline=False)
            
            tracked_count = len(bot.unverified_members.get(guild_id, {}))
            embed.add_field(name="Currently Tracking", value=f"{tracked_count} member(s)", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return
        
        # Update configuration
        if role is not None:
            config['role_name'] = role.name
        
        if kick_after_minutes is not None:
            if kick_after_minutes < 1:
                await interaction.response.send_message("❌ Kick time must be at least 1 minute.", ephemeral=False)
                return
            config['kick_after_minutes'] = kick_after_minutes
        
        bot.guild_configs[guild_id] = config
        bot.save_data()
        
        embed = discord.Embed(
            title="✅ Configuration Updated",
            description=f"Settings for **{interaction.guild.name}**",
            color=COLOR_SUCCESS
        )
        
        if role is not None:
            embed.add_field(name="Target Role", value=f"{role.mention} (`{role.name}`)", inline=False)
        
        if kick_after_minutes is not None:
            embed.add_field(name="Kick After", value=f"`{kick_after_minutes}` minutes", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
        
        # Rescan
        bot.unverified_members[guild_id] = {}
        from src.tasks import scan_existing_members
        await scan_existing_members(bot)
    
    @bot.tree.command(name="status", description="View all tracked unverified members")
    async def slash_status(interaction: discord.Interaction):
        """Slash command for status"""
        # Check permissions
        if not has_permission(bot, interaction):
            await interaction.response.send_message(
                get_permission_error_message(bot, interaction.guild.id),
                ephemeral=True
            )
            return
        
        guild_id = interaction.guild.id
        config = bot.get_guild_config(guild_id)
        
        if guild_id not in bot.unverified_members or not bot.unverified_members[guild_id]:
            await interaction.response.send_message("✅ No unverified members currently being tracked.", ephemeral=False)
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
            member = interaction.guild.get_member(member_id)
            
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
        
        from src.config import CHECK_INTERVAL_MINUTES
        embed.set_footer(text=f"Total: {len(bot.unverified_members[guild_id])} | Next check in ~{CHECK_INTERVAL_MINUTES} min")
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    @bot.tree.command(name="setlogchannel", description="Set the channel for kick logs")
    @app_commands.describe(channel="The channel where kick logs will be sent")
    async def slash_setlogchannel(interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the log channel for kick notifications"""
        # Check permissions
        if not has_permission(bot, interaction):
            await interaction.response.send_message(
                get_permission_error_message(bot, interaction.guild.id),
                ephemeral=True
            )
            return
        
        guild_id = interaction.guild.id
        config = bot.get_guild_config(guild_id)
        
        config['log_channel_id'] = channel.id
        bot.guild_configs[guild_id] = config
        bot.save_data()
        
        embed = discord.Embed(
            title="✅ Log Channel Set",
            description=f"Kick logs will now be sent to {channel.mention}",
            color=COLOR_SUCCESS
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
        
        # Send test log
        test_embed = discord.Embed(
            description="✅ **Log channel configured successfully**\nKick logs will appear here.",
            color=COLOR_SUCCESS,
            timestamp=datetime.now()
        )
        test_embed.set_footer(text="Auto-Kick System")
        
        try:
            await channel.send(embed=test_embed)
        except:
            await interaction.followup.send("⚠️ Make sure I have permissions to send messages!", ephemeral=False)
    
    @bot.tree.command(name="toggledm", description="Enable or disable DM notifications before kicking")
    @app_commands.describe(enabled="Turn DM notifications on or off")
    async def slash_toggledm(interaction: discord.Interaction, enabled: bool):
        """Toggle DM notifications"""
        # Check permissions
        if not has_permission(bot, interaction):
            await interaction.response.send_message(
                get_permission_error_message(bot, interaction.guild.id),
                ephemeral=True
            )
            return
        
        guild_id = interaction.guild.id
        config = bot.get_guild_config(guild_id)
        
        config['send_dm'] = enabled
        bot.guild_configs[guild_id] = config
        bot.save_data()
        
        status = "enabled ✅" if enabled else "disabled ❌"
        embed = discord.Embed(
            title="📬 DM Notifications",
            description=f"DM notifications are now **{status}**",
            color=COLOR_SUCCESS if enabled else COLOR_ERROR
        )
        
        if not enabled:
            embed.add_field(
                name="Note",
                value="Members will be kicked silently without warning.",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    @bot.tree.command(name="addrole", description="Add a staff role that can use bot commands")
    @app_commands.describe(role="The role to give bot permissions to")
    async def slash_addrole(interaction: discord.Interaction, role: discord.Role):
        """Add staff role with bot permissions"""
        # Only administrators can add roles
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Only Administrators can add staff roles.",
                ephemeral=True
            )
            return
        
        guild_id = interaction.guild.id
        config = bot.get_guild_config(guild_id)
        
        allowed_roles = config.get('allowed_roles', [])
        
        if role.name in allowed_roles:
            await interaction.response.send_message(
                f"⚠️ Role {role.mention} already has bot permissions!",
                ephemeral=False
            )
            return
        
        allowed_roles.append(role.name)
        config['allowed_roles'] = allowed_roles
        bot.guild_configs[guild_id] = config
        bot.save_data()
        
        embed = discord.Embed(
            title="✅ Staff Role Added",
            description=f"{role.mention} can now use bot commands",
            color=COLOR_SUCCESS
        )
        
        if len(allowed_roles) > 1:
            roles_list = "\n".join([f"• `{r}`" for r in allowed_roles])
            embed.add_field(name="All Staff Roles", value=roles_list, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    @bot.tree.command(name="removerole", description="Remove a staff role's bot permissions")
    @app_commands.describe(role="The role to remove bot permissions from")
    async def slash_removerole(interaction: discord.Interaction, role: discord.Role):
        """Remove staff role permissions"""
        # Only administrators can remove roles
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Only Administrators can remove staff roles.",
                ephemeral=True
            )
            return
        
        guild_id = interaction.guild.id
        config = bot.get_guild_config(guild_id)
        
        allowed_roles = config.get('allowed_roles', [])
        
        if role.name not in allowed_roles:
            await interaction.response.send_message(
                f"⚠️ Role {role.mention} doesn't have bot permissions!",
                ephemeral=False
            )
            return
        
        allowed_roles.remove(role.name)
        config['allowed_roles'] = allowed_roles
        bot.guild_configs[guild_id] = config
        bot.save_data()
        
        embed = discord.Embed(
            title="✅ Staff Role Removed",
            description=f"{role.mention} can no longer use bot commands",
            color=COLOR_SUCCESS
        )
        
        if allowed_roles:
            roles_list = "\n".join([f"• `{r}`" for r in allowed_roles])
            embed.add_field(name="Remaining Staff Roles", value=roles_list, inline=False)
        else:
            embed.add_field(name="Staff Roles", value="❌ None (Admin only)", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    @bot.tree.command(name="listroles", description="List all staff roles that can use bot commands")
    async def slash_listroles(interaction: discord.Interaction):
        """List staff roles"""
        # Check permissions
        if not has_permission(bot, interaction):
            await interaction.response.send_message(
                get_permission_error_message(bot, interaction.guild.id),
                ephemeral=True
            )
            return
        
        guild_id = interaction.guild.id
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
            embed.add_field(name="Staff Roles", value="❌ None configured\n\nOnly Administrators can use bot commands.", inline=False)
        
        embed.add_field(
            name="💡 How to Add Staff Roles",
            value="Use `/addrole @YourStaffRole` to give bot permissions",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    @bot.tree.command(name="help", description="Show all available commands")
    async def slash_help(interaction: discord.Interaction):
        """Show help message"""
        embed = discord.Embed(
            title="🤖 Auto-Kick Bot Commands",
            description="Automatically kick members who don't verify in time",
            color=COLOR_INFO
        )
        
        embed.add_field(
            name="📋 Basic Commands",
            value="`/setup` - Configure role and kick timer\n"
                  "`/status` - View tracked members\n"
                  "`/help` - Show this message",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Configuration",
            value="`/setlogchannel` - Set log channel\n"
                  "`/toggledm` - Enable/disable DMs",
            inline=False
        )
        
        embed.add_field(
            name="👥 Permission Management",
            value="`/addrole` - Give staff role bot permissions\n"
                  "`/removerole` - Remove role permissions\n"
                  "`/listroles` - List staff roles",
            inline=False
        )
        
        embed.add_field(
            name="🔊 Voice Commands",
            value="`/join` - Join a voice channel\n"
                  "`/disconnect` - Leave voice channel",
            inline=False
        )
        
        # Check if user has permissions
        if has_permission(bot, interaction):
            embed.set_footer(text="✅ You have permission to use these commands")
        else:
            embed.set_footer(text="⚠️ You don't have permission to use these commands")
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    @bot.tree.command(name="join", description="Join a voice channel")
    @app_commands.describe(channel="The voice channel to join")
    async def slash_join(interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Join a voice channel"""
        # Check permissions
        if not has_permission(bot, interaction):
            await interaction.response.send_message(
                get_permission_error_message(bot, interaction.guild.id),
                ephemeral=True
            )
            return
        
        # Check if bot is already in a voice channel in this guild
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.channel.id == channel.id:
                await interaction.response.send_message(
                    f"✅ Already connected to {channel.mention}",
                    ephemeral=False
                )
                return
            else:
                # Move to new channel
                await interaction.guild.voice_client.move_to(channel)
                embed = discord.Embed(
                    title="🔊 Voice Channel",
                    description=f"Moved to {channel.mention}",
                    color=COLOR_SUCCESS
                )
                await interaction.response.send_message(embed=embed, ephemeral=False)
                return
        
        # Join the voice channel
        try:
            await channel.connect()
            embed = discord.Embed(
                title="🔊 Voice Channel",
                description=f"Connected to {channel.mention}",
                color=COLOR_SUCCESS
            )
            embed.set_footer(text="Use /disconnect to leave")
            await interaction.response.send_message(embed=embed, ephemeral=False)
        except discord.ClientException:
            await interaction.response.send_message(
                "❌ Already connected to a voice channel. Use `/disconnect` first.",
                ephemeral=False
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ Missing permissions to join {channel.mention}",
                ephemeral=False
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error joining voice channel: {e}",
                ephemeral=False
            )
    
    @bot.tree.command(name="disconnect", description="Leave the voice channel")
    async def slash_disconnect(interaction: discord.Interaction):
        """Disconnect from voice channel"""
        # Check permissions
        if not has_permission(bot, interaction):
            await interaction.response.send_message(
                get_permission_error_message(bot, interaction.guild.id),
                ephemeral=True
            )
            return
        
        # Check if bot is in a voice channel
        if not interaction.guild.voice_client:
            await interaction.response.send_message(
                "❌ Not connected to any voice channel",
                ephemeral=False
            )
            return
        
        # Disconnect
        channel_name = interaction.guild.voice_client.channel.name
        await interaction.guild.voice_client.disconnect()
        
        embed = discord.Embed(
            title="🔊 Voice Channel",
            description=f"Disconnected from **{channel_name}**",
            color=COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)