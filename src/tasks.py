"""
Background tasks for the Auto-Kick Bot
"""
import discord
from discord.ext import tasks
from datetime import datetime, timedelta
from src.config import CHECK_INTERVAL_MINUTES


async def scan_existing_members(bot):
    """Scan all guilds for existing members with the unverified role"""
    print("\n🔍 Scanning for existing unverified members...")
    total_found = 0
    newly_tracked = 0
    
    for guild in bot.guilds:
        try:
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
                        bot.unverified_members[guild_id][member.id] = datetime.now().timestamp()
                        newly_tracked += 1
                        print(f"[{guild.name}] 🆕 New unverified member: {member.name}")
                    else:
                        original_time = datetime.fromtimestamp(bot.unverified_members[guild_id][member.id])
                        print(f"[{guild.name}] 🔄 Already tracking {member.name} (since {original_time.strftime('%H:%M:%S')})")
                    found_in_guild += 1
            
            if found_in_guild > 0:
                total_found += found_in_guild
            
            bot.save_data()
        except Exception as e:
            print(f"[{guild.name}] ❌ Error in scan: {e}")
            import traceback
            traceback.print_exc()
    
    if newly_tracked > 0:
        print(f"✅ Scan complete! Tracking {total_found} member(s) total ({newly_tracked} newly added)\n")
    else:
        print(f"✅ Scan complete! Tracking {total_found} member(s) total (all timestamps preserved)\n")


def setup_background_tasks(bot):
    """Setup and start background tasks"""
    
    print("🔧 Setting up background tasks...")
    
    @tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
    async def check_unverified_task():
        """Periodically check and kick members who have exceeded the time limit"""
        try:
            now = datetime.now()
            print(f"\n{'='*60}")
            print(f"🔍 AUTO-KICK CHECK: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            total_kicked = 0
            total_checked = 0
            
            for guild_id, members in list(bot.unverified_members.items()):
                try:
                    guild = bot.get_guild(guild_id)
                    
                    if not guild:
                        print(f"⚠️ Guild {guild_id} not found (bot may have been removed)")
                        continue
                    
                    config = bot.get_guild_config(guild_id)
                    kick_threshold = timedelta(minutes=config['kick_after_minutes'])
                    unverified_role = discord.utils.get(guild.roles, name=config['role_name'])
                    
                    if not unverified_role:
                        print(f"[{guild.name}] ⚠️ Role '{config['role_name']}' not found - skipping")
                        continue
                    
                    bot_member = guild.get_member(bot.user.id)
                    if not bot_member:
                        print(f"[{guild.name}] ⚠️ Bot member object not found - skipping")
                        continue
                    
                    print(f"\n[{guild.name}] (ID: {guild_id})")
                    print(f"  📋 Tracking: {len(members)} member(s)")
                    print(f"  ⏱️  Threshold: {config['kick_after_minutes']} minutes")
                    print(f"  🎭 Target role: {unverified_role.name}")
                    print(f"  🤖 Bot role: {bot_member.top_role.name} (position: {bot_member.top_role.position})")
                    
                    for member_id, join_timestamp in list(members.items()):
                        try:
                            total_checked += 1
                            join_time = datetime.fromtimestamp(join_timestamp)
                            time_elapsed = now - join_time
                            minutes_elapsed = int(time_elapsed.total_seconds() / 60)
                            
                            member = guild.get_member(member_id)
                            
                            if not member:
                                print(f"  🚪 Member {member_id} left server - removing from tracking")
                                del bot.unverified_members[guild_id][member_id]
                                bot.save_data()
                                continue
                            
                            # Check if member still has unverified role
                            if unverified_role not in member.roles:
                                print(f"  ✅ {member.name} verified! Removing from tracking")
                                del bot.unverified_members[guild_id][member_id]
                                bot.save_data()
                                continue
                            
                            # Check if time exceeded
                            if time_elapsed >= kick_threshold:
                                print(f"  ⏰ {member.name} ({member.id}) exceeded limit: {minutes_elapsed} min")
                                print(f"     └─ Member's highest role: {member.top_role.name} (position: {member.top_role.position})")
                                
                                # PRE-CHECK: Role hierarchy
                                if bot_member.top_role.position <= member.top_role.position:
                                    print(f"     └─ ❌ HIERARCHY ISSUE: Bot role ({bot_member.top_role.position}) <= User role ({member.top_role.position})")
                                    
                                    log_channel_id = config.get('log_channel_id')
                                    if log_channel_id:
                                        log_channel = guild.get_channel(log_channel_id)
                                        if log_channel:
                                            try:
                                                error_embed = discord.Embed(
                                                    title="⚠️ Auto-Kick Failed - Role Hierarchy",
                                                    description=f"Cannot kick **{member.mention}** `{member.name}`",
                                                    color=0xe74c3c,
                                                    timestamp=datetime.now()
                                                )
                                                error_embed.add_field(
                                                    name="❌ Issue",
                                                    value=f"Bot role: `{bot_member.top_role.name}` (pos: {bot_member.top_role.position})\n"
                                                          f"User role: `{member.top_role.name}` (pos: {member.top_role.position})\n\n"
                                                          f"Bot's role must have a **higher position number**",
                                                    inline=False
                                                )
                                                error_embed.add_field(
                                                    name="✅ Fix",
                                                    value=f"1. Go to **Server Settings → Roles**\n"
                                                          f"2. Drag `{bot_member.top_role.name}` **ABOVE** `{member.top_role.name}`\n"
                                                          f"3. Save changes",
                                                    inline=False
                                                )
                                                error_embed.add_field(
                                                    name="⏱️ Time Unverified",
                                                    value=f"`{minutes_elapsed}` minutes",
                                                    inline=True
                                                )
                                                error_embed.set_footer(text="User remains tracked • Will retry on next check")
                                                
                                                await log_channel.send(embed=error_embed)
                                            except Exception as e:
                                                print(f"     └─ ⚠️ Could not send log: {e}")
                                    continue
                                
                                # PRE-CHECK: Bot permissions
                                if not guild.me.guild_permissions.kick_members:
                                    print(f"     └─ ❌ BOT MISSING 'KICK MEMBERS' PERMISSION")
                                    
                                    log_channel_id = config.get('log_channel_id')
                                    if log_channel_id:
                                        log_channel = guild.get_channel(log_channel_id)
                                        if log_channel:
                                            try:
                                                error_embed = discord.Embed(
                                                    title="⚠️ Auto-Kick Failed - Missing Permission",
                                                    description=f"Cannot kick **{member.mention}** `{member.name}`",
                                                    color=0xe74c3c,
                                                    timestamp=datetime.now()
                                                )
                                                error_embed.add_field(
                                                    name="❌ Issue",
                                                    value="Bot is missing **Kick Members** permission",
                                                    inline=False
                                                )
                                                error_embed.add_field(
                                                    name="✅ Fix",
                                                    value=f"1. Go to **Server Settings → Roles**\n"
                                                          f"2. Find `{bot_member.top_role.name}` role\n"
                                                          f"3. Enable **Kick Members** permission",
                                                    inline=False
                                                )
                                                error_embed.set_footer(text="User remains tracked • Will retry on next check")
                                                
                                                await log_channel.send(embed=error_embed)
                                            except Exception as e:
                                                print(f"     └─ ⚠️ Could not send log: {e}")
                                    continue
                                
                                # Attempt kick
                                kick_successful = False
                                
                                try:
                                    await member.kick(reason=f"Auto-kick: Did not verify within {config['kick_after_minutes']} minutes")
                                    print(f"     └─ ✅ KICKED SUCCESSFULLY")
                                    kick_successful = True
                                    total_kicked += 1
                                    
                                except discord.Forbidden as e:
                                    print(f"     └─ ❌ FORBIDDEN ERROR: {e}")
                                    
                                    log_channel_id = config.get('log_channel_id')
                                    if log_channel_id:
                                        log_channel = guild.get_channel(log_channel_id)
                                        if log_channel:
                                            try:
                                                error_embed = discord.Embed(
                                                    title="⚠️ Auto-Kick Failed - Forbidden",
                                                    description=f"Cannot kick **{member.mention}** `{member.name}`",
                                                    color=0xe74c3c,
                                                    timestamp=datetime.now()
                                                )
                                                error_embed.add_field(
                                                    name="❌ Error",
                                                    value=f"```{str(e)}```",
                                                    inline=False
                                                )
                                                error_embed.add_field(
                                                    name="Possible Causes",
                                                    value="• User is server owner (cannot be kicked)\n"
                                                          "• Hidden role hierarchy issue\n"
                                                          "• Bot permissions issue",
                                                    inline=False
                                                )
                                                error_embed.set_footer(text="User remains tracked")
                                                
                                                await log_channel.send(embed=error_embed)
                                            except:
                                                pass
                                        
                                except Exception as e:
                                    print(f"     └─ ❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
                                    import traceback
                                    traceback.print_exc()
                                
                                # Post-kick actions
                                if kick_successful:
                                    try:
                                        await bot.log_kick(guild, member, minutes_elapsed)
                                    except Exception as e:
                                        print(f"     └─ ⚠️ Could not log kick: {e}")
                                    
                                    if guild_id in bot.unverified_members and member_id in bot.unverified_members[guild_id]:
                                        del bot.unverified_members[guild_id][member_id]
                                        bot.save_data()
                                else:
                                    print(f"     └─ 📌 Keeping in tracking list for retry")
                            
                        except Exception as e:
                            print(f"  ❌ Error processing member {member_id}: {e}")
                            import traceback
                            traceback.print_exc()
                
                except Exception as e:
                    print(f"❌ Error processing guild {guild_id}: {e}")
                    import traceback
                    traceback.print_exc()
            
            print(f"\n{'='*60}")
            print(f"✅ CHECK COMPLETE")
            print(f"   Checked: {total_checked} member(s)")
            print(f"   Kicked: {total_kicked} member(s)")
            print(f"{'='*60}\n")
            
            # Update bot status
            total_unverified = sum(len(members) for members in bot.unverified_members.values())
            await bot.change_presence(activity=discord.Game(name=f"🔍 Protecting • {total_unverified} pending"))
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR IN CHECK TASK: {e}")
            import traceback
            traceback.print_exc()
    
    @check_unverified_task.before_loop
    async def before_check_loop():
        """Wait for the bot to be ready before starting the loop"""
        print("⏳ Waiting for bot to be ready before starting auto-kick task...")
        await bot.wait_until_ready()
        print("✅ Bot ready! Starting auto-kick task...")
    
    @check_unverified_task.after_loop
    async def after_check_loop():
        """Called when the loop stops"""
        if check_unverified_task.is_being_cancelled():
            print("⚠️ Auto-kick task was cancelled")
        else:
            print("⚠️ Auto-kick task stopped")
    
    @check_unverified_task.error
    async def check_task_error(error):
        """Handle errors in the task loop"""
        print(f"❌ ERROR IN AUTO-KICK TASK: {error}")
        import traceback
        traceback.print_exc()
    
    # Start the task
    check_unverified_task.start()
    print("✅ Auto-kick background task started!")
    
    return check_unverified_task