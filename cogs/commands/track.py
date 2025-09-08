import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import datetime

class Track(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "db/track.db"
        self.bot.loop.create_task(self.setup_db())
        self.status_check.start()
        self.status_cache = {}

    async def setup_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tracking (
                    guild_id INTEGER,
                    bot_id INTEGER,
                    channel_id INTEGER,
                    role_id INTEGER,
                    last_online TIMESTAMP,
                    last_offline TIMESTAMP
                )""")
            await db.commit()

    def is_admin():
        async def predicate(ctx):
            if isinstance(ctx, commands.Context):
                return ctx.author.guild_permissions.administrator
            elif isinstance(ctx, discord.Interaction):
                return ctx.user.guild_permissions.administrator
            return False
        return commands.check(predicate)

    @commands.hybrid_group(name="track", with_app_command=True, description="Track help menu")
    @is_admin()
    async def track(self, ctx):
        embed = discord.Embed(
            title="📡 Bot Tracker System",
            description=(
                "Track bot online/offline status changes.\n\n"
                "**🧭 Commands:**\n"
                "track add — Add tracking\n"
                "track delete — Delete tracking\n"
                "track config — View tracking config\n"
                "track clear — Clear all tracked bots\n"
                "track stats — Show tracking stats\n"
                "track test — Simulate status change"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Flenzo Bot • Bot Status Tracker")
        await ctx.reply(embed=embed)

    @track.command(name="add", description="Track a bot's online/offline status")
    @app_commands.describe(bot="The bot to track", channel="Channel to log status", role="Optional role to ping")
    @is_admin()
    async def add(self, ctx, bot: discord.Member, channel: discord.TextChannel, role: discord.Role = None):
        if not bot.bot:
            return await ctx.reply(embed=discord.Embed(description="<:icon_cross:1381448030481547315> That user is not a bot.", color=discord.Color.red()))

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM tracking WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                count = (await cursor.fetchone())[0]
                if count >= 5:
                    return await ctx.reply(embed=discord.Embed(description="<:icon_cross:1381448030481547315> You can only track up to 5 bots per server.", color=discord.Color.red()))
            await db.execute("REPLACE INTO tracking (guild_id, bot_id, channel_id, role_id, last_online, last_offline) VALUES (?, ?, ?, ?, NULL, NULL)",
                             (ctx.guild.id, bot.id, channel.id, role.id if role else None))
            await db.commit()

        await ctx.reply(embed=discord.Embed(description=f"<:IconTick:1381245157759782975> Now tracking `{bot.name}` in {channel.mention}!", color=discord.Color.green()))

    @track.command(name="delete", description="Stop tracking a bot")
    @app_commands.describe(bot="The bot to stop tracking")
    @is_admin()
    async def delete(self, ctx, bot: discord.Member):
        if not bot.bot:
            return await ctx.reply(embed=discord.Embed(description="<:icon_cross:1381448030481547315> That user is not a bot.", color=discord.Color.red()))

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM tracking WHERE guild_id = ? AND bot_id = ?", (ctx.guild.id, bot.id))
            await db.commit()

        await ctx.reply(embed=discord.Embed(description=f"<:IconTick:1381245157759782975> Stopped tracking `{bot.name}`.", color=discord.Color.green()))

    @track.command(name="config", description="View your current tracking configuration")
    @is_admin()
    async def config(self, ctx):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT bot_id, channel_id, role_id FROM tracking WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    return await ctx.reply(embed=discord.Embed(description="<:icon_cross:1381448030481547315> No bots are currently being tracked.", color=discord.Color.red()))

                embed = discord.Embed(title="🔧 Tracking Configuration", color=discord.Color.blurple())
                for bot_id, channel_id, role_id in rows:
                    bot = ctx.guild.get_member(bot_id)
                    channel = ctx.guild.get_channel(channel_id)
                    role = ctx.guild.get_role(role_id) if role_id else None
                    embed.add_field(
                        name=bot.name if bot else f"<Unknown {bot_id}>",
                        value=f"Channel: {channel.mention if channel else f'<#{channel_id}>'}\nRole: {role.mention if role else '`None`'}",
                        inline=False
                    )
                await ctx.reply(embed=embed)

    @track.command(name="clear", description="Remove all tracked bots")
    @is_admin()
    async def clear(self, ctx):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM tracking WHERE guild_id = ?", (ctx.guild.id,))
            await db.commit()
        await ctx.reply(embed=discord.Embed(description="<:IconTick:1381245157759782975> All tracked bots have been cleared.", color=discord.Color.green()))

    @track.command(name="stats", description="Show tracking stats")
    @is_admin()
    async def stats(self, ctx):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM tracking WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                count = (await cursor.fetchone())[0]
        embed = discord.Embed(title="📊 Tracking Stats", description=f"You're tracking `{count}` out of 5 allowed bots.", color=discord.Color.blurple())
        await ctx.reply(embed=embed)

    @track.command(name="test", description="Send a test online/offline embed")
    @app_commands.describe(bot="The bot to simulate", status="online or offline")
    @is_admin()
    async def test(self, ctx, bot: discord.Member, status: str):
        status = status.lower()
        if not bot.bot or status not in ["online", "offline"]:
            return await ctx.reply(embed=discord.Embed(description="<:icon_cross:1381448030481547315> Invalid bot or status.", color=discord.Color.red()))

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT channel_id, role_id FROM tracking WHERE guild_id = ? AND bot_id = ?", (ctx.guild.id, bot.id)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return await ctx.reply(embed=discord.Embed(description="<:icon_cross:1381448030481547315> This bot is not being tracked.", color=discord.Color.red()))
                channel_id, role_id = row
                channel = ctx.guild.get_channel(channel_id)
                if not channel:
                    return await ctx.reply(embed=discord.Embed(description="<:icon_cross:1381448030481547315> Tracking channel not found.", color=discord.Color.red()))

                embed = discord.Embed(
                    title=f"{'<a:uptimer:1398574092298227802> Bot Online' if status == 'online' else '<a:Downtime:1398574068390953064> Bot Offline'}",
                    description=f"{bot.mention} is now **{status.upper()}**",
                    color=discord.Color.green() if status == "online" else discord.Color.red()
                )
                ping = f"<@&{role_id}>" if role_id else ""
                await channel.send(content=ping, embed=embed)
                await ctx.reply(embed=discord.Embed(description="<:IconTick:1381245157759782975> Test notification sent.", color=discord.Color.green()))

    @tasks.loop(seconds=30)
    async def status_check(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT guild_id, bot_id, channel_id, role_id, last_online, last_offline FROM tracking") as cursor:
                rows = await cursor.fetchall()
                for guild_id, bot_id, channel_id, role_id, last_online, last_offline in rows:
                    guild = self.bot.get_guild(guild_id)
                    if not guild:
                        continue
                    member = guild.get_member(bot_id)
                    if not member:
                        continue
                    current_status = str(member.status)
                    online_states = ['online', 'idle', 'dnd']
                    is_online = current_status in online_states
                    cache_key = (guild_id, bot_id)
                    last_known = self.status_cache.get(cache_key)
                    now = datetime.datetime.utcnow()

                    if is_online:
                        if last_known == "offline":
                            channel = guild.get_channel(channel_id)
                            if channel:
                                embed = discord.Embed(title="<a:uptimer:1398574092298227802> Bot Online", color=discord.Color.green())
                                embed.add_field(name="The Bot", value=f"{member.mention} is now **online**")
                                embed.timestamp = now
                                ping = f"<@&{role_id}>" if role_id else ""
                                await channel.send(content=ping, embed=embed)
                            await db.execute("UPDATE tracking SET last_online = ? WHERE guild_id = ? AND bot_id = ?", (now.isoformat(), guild_id, bot_id))
                    else:
                        if last_known in ["online", "idle", "dnd"]:
                            channel = guild.get_channel(channel_id)
                            if channel:
                                embed = discord.Embed(title="<a:Downtime:1398574068390953064> Bot Offline", color=discord.Color.red())
                                embed.add_field(name="The Bot", value=f"{member.mention} is now **offline**")
                                embed.timestamp = now
                                ping = f"<@&{role_id}>" if role_id else ""
                                await channel.send(content=ping, embed=embed)
                            await db.execute("UPDATE tracking SET last_offline = ? WHERE guild_id = ? AND bot_id = ?", (now.isoformat(), guild_id, bot_id))

                    self.status_cache[cache_key] = current_status
            await db.commit()

    @status_check.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Track(bot))