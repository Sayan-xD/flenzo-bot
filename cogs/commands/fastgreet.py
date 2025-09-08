import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import asyncio
import os

DB_PATH = "./db/fastgreet.db"

class FastGreet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.makedirs("./db", exist_ok=True)
        self.init_db()

    def init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS greet_channels (
                    guild_id INTEGER,
                    channel_id INTEGER,
                    PRIMARY KEY (guild_id, channel_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS greet_messages (
                    guild_id INTEGER PRIMARY KEY,
                    message TEXT
                )
            """)

    # ========== HYBRID COMMAND GROUP ==========

    @commands.hybrid_group(name="fastgreet", invoke_without_command=True, with_app_command=True)
    async def fastgreet(self, ctx):
        embed = discord.Embed(
            title="Fastgreet [7]",
            description="`<>` Required | `[]` Optional",
            color=discord.Color.blue()
        )
        embed.add_field(name="fastgreet enable", value="Enable greet system in a channel.", inline=False)
        embed.add_field(name="fastgreet disable", value="Disable greet system from a channel.", inline=False)
        embed.add_field(name="fastgreet list", value="List all greet-enabled channels.", inline=False)
        embed.add_field(name="fastgreet setmessage", value="Set a custom greet message using variables.", inline=False)
        embed.add_field(name="fastgreet viewmessage", value="View current greet message.", inline=False)
        embed.add_field(name="fastgreet variables", value="Show all available message variables.", inline=False)
        embed.add_field(name="fastgreet test", value="Test your greet message as if you joined.", inline=False)
        await ctx.reply(embed=embed)

    @fastgreet.command(name="enable", description="Enable fastgreet in a channel.")
    @app_commands.describe(channel="Channel to enable greeting in")
    async def enable(self, ctx: commands.Context, channel: discord.TextChannel):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT OR IGNORE INTO greet_channels (guild_id, channel_id) VALUES (?, ?)",
                         (ctx.guild.id, channel.id))
        await ctx.reply(f"<:IconTick:1381245157759782975> Enabled fastgreet in {channel.mention}")

    @fastgreet.command(name="disable", description="Disable fastgreet in a channel.")
    @app_commands.describe(channel="Channel to disable greeting in")
    async def disable(self, ctx: commands.Context, channel: discord.TextChannel):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM greet_channels WHERE guild_id = ? AND channel_id = ?",
                         (ctx.guild.id, channel.id))
        await ctx.reply(f"<:IconTick:1381245157759782975> Disabled fastgreet in {channel.mention}")

    @fastgreet.command(name="list", description="List all greet-enabled channels.")
    async def list(self, ctx: commands.Context):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT channel_id FROM greet_channels WHERE guild_id = ?", (ctx.guild.id,))
            rows = cursor.fetchall()

        if not rows:
            await ctx.reply("⚠️ No greet channels configured.")
        else:
            channels = [f"<#{row[0]}>" for row in rows]
            await ctx.reply("📋 Greet Channels:\n" + ", ".join(channels))

    @fastgreet.command(name="setmessage", description="Set custom greet message with variables.")
    @app_commands.describe(message="Message with placeholders like {user}, {server}, etc.")
    async def setmessage(self, ctx: commands.Context, *, message: str):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO greet_messages (guild_id, message)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET message=excluded.message
            """, (ctx.guild.id, message))
        await ctx.reply("<:IconTick:1381245157759782975> Greet message set.")

    @fastgreet.command(name="viewmessage", description="View current greet message.")
    async def viewmessage(self, ctx: commands.Context):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT message FROM greet_messages WHERE guild_id = ?", (ctx.guild.id,))
            row = cursor.fetchone()

        if row:
            await ctx.reply(f"📝 Greet message:\n```{row[0]}```")
        else:
            await ctx.reply("⚠️ No greet message set. Default will be used.")

    @fastgreet.command(name="variables", description="Show all fastgreet variables.")
    async def variables(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Fastgreet Variables",
            color=discord.Color.green(),
            description="Use these variables in your greet message:"
        )
        embed.add_field(name="{user} / {mention}", value="Mention of the user", inline=False)
        embed.add_field(name="{username}", value="Username only (no tag)", inline=False)
        embed.add_field(name="{tag}", value="Full tag (e.g. User#0001)", inline=False)
        embed.add_field(name="{server}", value="Server name", inline=False)
        embed.add_field(name="{count}", value="Server member count", inline=False)
        await ctx.reply(embed=embed)

    @fastgreet.command(name="test", description="Send the greet message to test it.")
    async def test(self, ctx: commands.Context):
        member = ctx.author
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT channel_id FROM greet_channels WHERE guild_id = ?", (ctx.guild.id,))
            channels = [row[0] for row in cursor.fetchall()]

            cursor = conn.execute("SELECT message FROM greet_messages WHERE guild_id = ?", (ctx.guild.id,))
            row = cursor.fetchone()
            msg = row[0] if row else "👋 {user} Welcome to {server}!"

        formatted = msg \
            .replace("{user}", member.mention) \
            .replace("{mention}", member.mention) \
            .replace("{username}", member.name) \
            .replace("{tag}", str(member)) \
            .replace("{server}", member.guild.name) \
            .replace("{count}", str(member.guild.member_count))

        sent = False
        for channel_id in channels:
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(formatted)
                    sent = True
                except discord.Forbidden:
                    continue

        if sent:
            await ctx.reply(f"<:IconTick:1381245157759782975> Test message sent.")
        else:
            await ctx.reply("⚠️ No active greet channels or I lack permission to send.")

    # ========== REAL GREETING EVENT ==========

    @commands.Cog.listener()
    async def on_member_join(self, member):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT channel_id FROM greet_channels WHERE guild_id = ?", (member.guild.id,))
            channels = [row[0] for row in cursor.fetchall()]

            cursor = conn.execute("SELECT message FROM greet_messages WHERE guild_id = ?", (member.guild.id,))
            row = cursor.fetchone()
            msg = row[0] if row else "👋 {user} Welcome to {server}!"

        formatted = msg \
            .replace("{user}", member.mention) \
            .replace("{mention}", member.mention) \
            .replace("{username}", member.name) \
            .replace("{tag}", str(member)) \
            .replace("{server}", member.guild.name) \
            .replace("{count}", str(member.guild.member_count))

        for channel_id in channels:
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    message = await channel.send(formatted)
                    await asyncio.sleep(2)
                    await message.delete()
                except discord.Forbidden:
                    continue

async def setup(bot):
    await bot.add_cog(FastGreet(bot))