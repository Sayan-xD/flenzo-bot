import discord
from discord.ext import commands
import aiosqlite
import datetime

PREMIUM_DB = "premium.db"

PREMIUM_TIERS = {
    "bronze": 30,
    "silver": 90,
    "gold": 180,
    "platinum": 365,
    "diamond": None
}

PREMIUM_ROLE_ID = 1395973150172254339
PREMIUM_LOG_CHANNEL_ID = 1389300355988197576
PREMIUM_GUILD_ID = 968855422423404606

SUPPORT_SERVER = "https://discord.gg/bGVYcmBdgE"

def is_premium():
    async def predicate(ctx):
        async with aiosqlite.connect(PREMIUM_DB) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS premium_users (
                    user_id INTEGER PRIMARY KEY,
                    tier TEXT,
                    expires_at TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS premium_guilds (
                    guild_id INTEGER PRIMARY KEY,
                    tier TEXT,
                    expires_at TEXT
                )
            """)
            await db.commit()

            # Check user
            user = await db.execute_fetchone("SELECT * FROM premium_users WHERE user_id = ?", (ctx.author.id,))
            # Check guild
            guild = await db.execute_fetchone("SELECT * FROM premium_guilds WHERE guild_id = ?", (ctx.guild.id if ctx.guild else 0,))

            now = datetime.datetime.utcnow()

            def valid(row):
                if row is None:
                    return False
                if row[2] is None:
                    return True
                return now < datetime.datetime.fromisoformat(row[2])

            if valid(user) or valid(guild):
                return True
            else:
                embed = discord.Embed(
                    title="⛔ Premium Only Command",
                    description=f"This command is only available to premium users.\n[Join Support Server]({SUPPORT_SERVER}) to get access.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return False

    return commands.check(predicate)

class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.initialize_database())

    async def initialize_database(self):
        async with aiosqlite.connect(PREMIUM_DB) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS premium_users (
                    user_id INTEGER PRIMARY KEY,
                    tier TEXT,
                    expires_at TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS premium_guilds (
                    guild_id INTEGER PRIMARY KEY,
                    tier TEXT,
                    expires_at TEXT
                )
            """)
            await db.commit()

    async def log_premium(self, embed: discord.Embed):
        log_channel = self.bot.get_channel(PREMIUM_LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)

    async def assign_premium_role(self, user: discord.User):
        guild = self.bot.get_guild(PREMIUM_GUILD_ID)
        if not guild:
            return
        member = guild.get_member(user.id)
        if member:
            role = guild.get_role(PREMIUM_ROLE_ID)
            if role:
                await member.add_roles(role)

    async def remove_premium_role(self, user: discord.User):
        guild = self.bot.get_guild(PREMIUM_GUILD_ID)
        if not guild:
            return
        member = guild.get_member(user.id)
        if member:
            role = guild.get_role(PREMIUM_ROLE_ID)
            if role:
                await member.remove_roles(role)

    @commands.group(name="premium", aliases=["pre", "prime"], invoke_without_command=True)
    @commands.is_owner()
    async def premium(self, ctx):
        await ctx.send_help(ctx.command)

    @premium.command(name="add")
    @commands.is_owner()
    async def premium_add(self, ctx, mode: str, target: discord.User | discord.Guild, tier: str):
        tier = tier.lower()
        if tier not in PREMIUM_TIERS:
            return await ctx.send("Invalid tier.")

        expires = None
        if PREMIUM_TIERS[tier] is not None:
            expires = datetime.datetime.utcnow() + datetime.timedelta(days=PREMIUM_TIERS[tier])

        async with aiosqlite.connect(PREMIUM_DB) as db:
            if mode == "user":
                await db.execute(
                    "REPLACE INTO premium_users (user_id, tier, expires_at) VALUES (?, ?, ?)",
                    (target.id, tier, expires.isoformat() if expires else None)
                )
                await self.assign_premium_role(target)
                embed = discord.Embed(
                    title="✅ Premium Granted",
                    description=f"User: {target.mention}\nTier: `{tier}`\nExpires: `{expires or 'Never'}`",
                    color=discord.Color.green()
                )
            elif mode == "guild":
                await db.execute(
                    "REPLACE INTO premium_guilds (guild_id, tier, expires_at) VALUES (?, ?, ?)",
                    (target.id, tier, expires.isoformat() if expires else None)
                )
                embed = discord.Embed(
                    title="✅ Premium Granted",
                    description=f"Guild: `{target.name}`\nTier: `{tier}`\nExpires: `{expires or 'Never'}`",
                    color=discord.Color.green()
                )
            else:
                return await ctx.send("Invalid mode. Use `user` or `guild`.")
            await db.commit()
            await self.log_premium(embed)
            await ctx.send(embed=embed)

    @premium.command(name="remove")
    @commands.is_owner()
    async def premium_remove(self, ctx, mode: str, target: discord.User | discord.Guild):
        async with aiosqlite.connect(PREMIUM_DB) as db:
            if mode == "user":
                await db.execute("DELETE FROM premium_users WHERE user_id = ?", (target.id,))
                await self.remove_premium_role(target)
                embed = discord.Embed(
                    title="❌ Premium Removed",
                    description=f"User: {target.mention}",
                    color=discord.Color.red()
                )
            elif mode == "guild":
                await db.execute("DELETE FROM premium_guilds WHERE guild_id = ?", (target.id,))
                embed = discord.Embed(
                    title="❌ Premium Removed",
                    description=f"Guild: `{target.name}`",
                    color=discord.Color.red()
                )
            else:
                return await ctx.send("Invalid mode. Use `user` or `guild`.")
            await db.commit()
            await self.log_premium(embed)
            await ctx.send(embed=embed)

    @premium.command(name="status")
    async def premium_status(self, ctx, mode: str, target: discord.User | discord.Guild = None):
        target = target or (ctx.author if mode == "user" else ctx.guild)
        async with aiosqlite.connect(PREMIUM_DB) as db:
            if mode == "user":
                row = await db.execute_fetchone("SELECT tier, expires_at FROM premium_users WHERE user_id = ?", (target.id,))
            elif mode == "guild":
                row = await db.execute_fetchone("SELECT tier, expires_at FROM premium_guilds WHERE guild_id = ?", (target.id,))
            else:
                return await ctx.send("Invalid mode.")

            if row:
                tier, expires_at = row
                embed = discord.Embed(
                    title="🌟 Premium Status",
                    description=f"{'User' if mode=='user' else 'Guild'}: {target.mention if mode=='user' else target.name}\nTier: `{tier}`\nExpires: `{expires_at or 'Never'}`",
                    color=discord.Color.gold()
                )
            else:
                embed = discord.Embed(
                    title="❌ No Premium Found",
                    description=f"{'User' if mode=='user' else 'Guild'}: {target.mention if mode=='user' else target.name}",
                    color=discord.Color.red()
                )
            await ctx.send(embed=embed)

    @premium.command(name="list")
    @commands.is_owner()
    async def premium_list(self, ctx):
        async with aiosqlite.connect(PREMIUM_DB) as db:
            users = await db.execute_fetchall("SELECT user_id, tier, expires_at FROM premium_users")
            guilds = await db.execute_fetchall("SELECT guild_id, tier, expires_at FROM premium_guilds")

        user_lines = [f"<@{uid}> — `{tier}` — Expires: `{exp or 'Never'}`" for uid, tier, exp in users]
        guild_lines = [f"`{self.bot.get_guild(gid).name if self.bot.get_guild(gid) else gid}` — `{tier}` — Expires: `{exp or 'Never'}`" for gid, tier, exp in guilds]

        embed = discord.Embed(title="📜 Premium List", color=discord.Color.blue())
        embed.add_field(name="Users", value="\n".join(user_lines) or "None", inline=False)
        embed.add_field(name="Guilds", value="\n".join(guild_lines) or "None", inline=False)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Premium(bot))