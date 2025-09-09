import json, sys, os
import discord
from discord.ext import commands
from core import Context
import aiosqlite
import asyncio

# ──────────────── DB Setup ────────────────

async def setup_db():
    async with aiosqlite.connect('db/prefix.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS prefixes (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT NOT NULL
            )
        ''')
        await db.commit()

asyncio.run(setup_db())

# ──────────────── Top Role Check ────────────────

async def is_topcheck_enabled(guild_id: int):
    async with aiosqlite.connect('db/topcheck.db') as db:
        async with db.execute("SELECT enabled FROM topcheck WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None and row[0] == 1

# ──────────────── JSON Config Helpers ────────────────

def read_json(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"guilds": {}}

def write_json(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def get_or_create_guild_config(file_path, guild_id, default_config):
    data = read_json(file_path)
    if "guilds" not in data:
        data["guilds"] = {}

    gid = str(guild_id)
    if gid not in data["guilds"]:
        data["guilds"][gid] = default_config
        write_json(file_path, data)

    return data["guilds"][gid]

def update_guild_config(file_path, guild_id, new_data):
    data = read_json(file_path)
    if "guilds" not in data:
        data["guilds"] = {}

    data["guilds"][str(guild_id)] = new_data
    write_json(file_path, data)

# ──────────────── Ignore Config ────────────────

def getIgnore(guild_id):
    default_config = {
        "channel": [],
        "role": None,
        "user": [],
        "bypassrole": None,
        "bypassuser": [],
        "commands": []
    }
    return get_or_create_guild_config("ignore.json", guild_id, default_config)

def updateignore(guild_id, data):
    update_guild_config("ignore.json", guild_id, data)

# ──────────────── Prefix System ────────────────

async def getConfig(guildID):
    async with aiosqlite.connect('db/prefix.db') as db:
        async with db.execute("SELECT prefix FROM prefixes WHERE guild_id = ?", (guildID,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"prefix": row[0]}
            else:
                default = {"prefix": "?"}
                await updateConfig(guildID, default)
                return default

async def updateConfig(guildID, data):
    async with aiosqlite.connect('db/prefix.db') as db:
        await db.execute(
            "INSERT OR REPLACE INTO prefixes (guild_id, prefix) VALUES (?, ?)",
            (guildID, data["prefix"])
        )
        await db.commit()

# ──────────────── System ────────────────

def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)

# ──────────────── Blacklist System ────────────────

def blacklist_check():
    async def predicate(ctx):
        async with aiosqlite.connect('db/block.db') as db:
            cursor = await db.execute("SELECT 1 FROM user_blacklist WHERE user_id = ?", (str(ctx.author.id),))
            if await cursor.fetchone():
                return False

            cursor = await db.execute("SELECT 1 FROM guild_blacklist WHERE guild_id = ?", (str(ctx.guild.id),))
            if await cursor.fetchone():
                return False

        return True
    return commands.check(predicate)

# ──────────────── Ignore Check (Fixed) ────────────────

async def get_ignore_data(guild_id: int) -> dict:
    async with aiosqlite.connect("db/ignore.db") as db:
        data = {
            "channel": set(),
            "user": set(),
            "command": set(),
            "bypassuser": set(),
        }

        async with db.execute("SELECT channel_id FROM ignored_channels WHERE guild_id = ?", (guild_id,)) as cursor:
            data["channel"] = {str(row[0]) for row in await cursor.fetchall()}

        async with db.execute("SELECT user_id FROM ignored_users WHERE guild_id = ?", (guild_id,)) as cursor:
            data["user"] = {str(row[0]) for row in await cursor.fetchall()}

        async with db.execute("SELECT command_name FROM ignored_commands WHERE guild_id = ?", (guild_id,)) as cursor:
            data["command"] = {row[0].strip().lower() for row in await cursor.fetchall()}

        async with db.execute("SELECT user_id FROM bypassed_users WHERE guild_id = ?", (guild_id,)) as cursor:
            data["bypassuser"] = {str(row[0]) for row in await cursor.fetchall()}

    return data

def ignore_check():
    async def predicate(ctx):
        data = await get_ignore_data(ctx.guild.id)
        if str(ctx.author.id) in data["bypassuser"]:
            return True
        if str(ctx.channel.id) in data["channel"] or str(ctx.author.id) in data["user"]:
            return False
        cmd = ctx.command.name.lower() if ctx.command else None
        if cmd in data["command"]:
            return False
        if hasattr(ctx.command, "aliases"):
            if any(alias.lower() in data["command"] for alias in ctx.command.aliases):
                return False
        return True
    return commands.check(predicate)

# ──────────────── Top Role Check ────────────────

def top_check():
    async def predicate(ctx):
        if not ctx.guild or ctx.invoked_with in ["help", "h"]:
            return True

        if not await is_topcheck_enabled(ctx.guild.id):
            return True

        if ctx.author != ctx.guild.owner and ctx.author.top_role.position <= ctx.guild.me.top_role.position:
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Your top role must be higher than my top role.",
                color=0x000000
            )
            embed.set_footer(
                text=f"Command: {ctx.command.qualified_name} | User: {ctx.author}",
                icon_url=ctx.author.display_avatar.url
            )
            await ctx.send(embed=embed)
            return False
        return True
    return commands.check(predicate)

# ──────────────── Premium Check ────────────────

def is_premium():
    def predicate(ctx):
        try:
            with open("premium.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return False

        if str(ctx.author.id) not in data:
            raise commands.CheckFailure("❌ This command is only for premium users.")
        return True
    return commands.check(predicate)