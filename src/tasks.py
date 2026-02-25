"""
Background tasks for the Auto-Kick Bot
"""
import discord
from discord.ext import tasks
from datetime import datetime, timedelta
from src.config import CHECK_INTERVAL_MINUTES
from src.utils import send_kick_log


async def scan_existing_members(bot):
    """Scan all guilds for existing members with the unverified role"""
    print("\n🔍 Scanning for existing unverified members...")
    total_found = 0
    newly_tracked = 0
    
    for guild in bot.guilds:
        config = bot.get_guild_config(guild.id)
        unverified_role = discord.utils.get(guild.roles, name=config['role_name'])
        
        if not unverified_role:
            print(f"[{guild.name}] ⚠️ Warning: '{config['role_name']}' role not found")
            continue
        
        guild_id = guild.id
        if guild_id not in bot.unverified_members:
            bot.unverified_members[guild_id] = {}
        
        found_in_guild = 0
        for member in guild.members:
            if unverified_role in member.roles:
                if member.id not in bot.unverified_members[guild_id]:
                    # Only add NEW members with current timestamp
                    # Existing tracked members keep their original timestamp
                    bot.unverified_members[guild_id][member.id] = datetime.now().timestamp()
                    newly_tracked += 1
                    print(f"[{guild.name}] 🆕 New unverified member: {member.name}")
                else:
                    # Member already tracked - keep existing timestamp
                    original_time = datetime.fromtimestamp(bot.unverified_members[guild_id][member.id])
                    print(f"[{guild.name}] 🔄 Already tracking {member.name} (since {original_time.strftime('%H:%M:%S')})")
                found_in_guild += 1
        
        if found_in_guild > 0:
            total_found += found_in_guild
        
        bot.save_data()
    
    if newly_tracked > 0:
        print(f"✅ Scan complete! Tracking {total_found} member(s) total ({newly_tracked} newly added)\n")
    else:
        print(f"✅ Scan complete! Tracking {total_found} member(s) total (all timestamps preserved)\n")


def setup_background_tasks(bot):
    """Setup and start background tasks"""
    
    @tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
    async def check_unverified_task():
        """Periodically check and kick members who have exceeded the time limit"""
        now = datetime.now()
        print(f"\n🔍 Running auto-kick check at {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_kicked = 0
        
        for guild_id, members in list(bot.unverified_members.items()):
            guild = bot.get_guild(guild_id)
            
            if not guild:
                continue
            
            config = bot.get_guild_config(guild_id)
            kick_threshold = timedelta(minutes=config['kick_after_minutes'])
            
            print(f"[{guild.name}] Checking {len(members)} tracked member(s)")
            
            for member_id, join_timestamp in list(members.items()):
                join_time = datetime.fromtimestamp(join_timestamp)
                time_elapsed = now - join_time
                
                member = guild.get_member(member_id)
                
                if not member:
                    del bot.unverified_members[guild_id][member_id]
                    bot.save_data()
                    continue
                
                minutes_elapsed = int(time_elapsed.total_seconds() / 60)
                
                if time_elapsed >= kick_threshold:
                    print(f"  ⏰ {member.name} exceeded time limit ({minutes_elapsed} min)")
                    
                    kick_successful = False  # Track if kick succeeded

                    # Try to send DM (optional, after successful kick)
                    if config.get('send_dm', False):
                        try:
                            await member.send(
                                f"⚠️ You have been removed from **{guild.name}** because "
                                f"you did not verify within {config['kick_after_minutes']} minutes."
                            )
                            print(f"  ✅ Sent DM to {member.name}")
                        except:
                            print(f"  ℹ️ Could not DM {member.name} (DMs disabled)")
                    
                    # Kick the member FIRST
                    try:
                        await member.kick(reason=f"Auto-kick: Did not verify within {config['kick_after_minutes']} minutes")
                        print(f"  ✅ Kicked {member.name}")
                        kick_successful = True
                        total_kicked += 1
                        
                    except discord.Forbidden:
                        print(f"  ❌ Missing permissions to kick {member.name}")
                        kick_successful = False
                        
                        # Log permission error to channel
                        log_channel_id = config.get('log_channel_id')
                        if log_channel_id:
                            log_channel = guild.get_channel(log_channel_id)
                            if log_channel:
                                error_embed = discord.Embed(
                                    title="⚠️ Auto-Kick Failed",
                                    description=f"Unable to kick **{member.mention}** ({member.name})",
                                    color=0xe74c3c,  # Red
                                    timestamp=datetime.now()
                                )
                                error_embed.add_field(
                                    name="Reason",
                                    value="Missing permissions or role hierarchy issue",
                                    inline=False
                                )
                                error_embed.add_field(
                                    name="Solution",
                                    value="Make sure the bot's role is **above** the user's highest role in Server Settings → Roles",
                                    inline=False
                                )
                                error_embed.add_field(
                                    name="Time Unverified",
                                    value=f"`{minutes_elapsed} minutes`",
                                    inline=True
                                )
                                error_embed.set_footer(text="Auto-Kick System • User will be retried on next check")
                                
                                try:
                                    await log_channel.send(embed=error_embed)
                                except:
                                    pass
                        kick_successful = False
                    except Exception as e:
                        print(f"  ❌ Error kicking {member.name}: {e}")
                        kick_successful = False
                    
                    # Only send DM and log if kick was successful
                    if kick_successful:
                        
                        # Log to channel
                        await bot.log_kick(guild, member, minutes_elapsed)
                        
                        # Remove from tracking (only if kicked successfully)
                        if guild_id in bot.unverified_members and member_id in bot.unverified_members[guild_id]:
                            del bot.unverified_members[guild_id][member_id]
                            bot.save_data()
                    else:
                        # Kick failed - keep tracking the member
                        print(f"  ⚠️ {member.name} still being tracked (kick failed)")
        
        if total_kicked > 0:
            print(f"✅ Check complete - {total_kicked} member(s) kicked")
        else:
            print(f"✅ Check complete - no kicks needed")
    
    @check_unverified_task.before_loop
    async def before_check_loop():
        """Wait for the bot to be ready before starting the loop"""
        await bot.wait_until_ready()
    
    # Start the task
    check_unverified_task.start()
    
    return check_unverified_task
