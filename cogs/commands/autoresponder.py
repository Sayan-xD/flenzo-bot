import discord
from discord.ext import commands
import aiosqlite
import os
import json
from utils.Tools import *

DB_PATH = "db/autoresponder.db"

class AutoResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.initialize_db())

    async def initialize_db(self):
        if not os.path.exists(os.path.dirname(DB_PATH)):
            os.makedirs(os.path.dirname(DB_PATH))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS autoresponses (
                    guild_id INTEGER,
                    name TEXT,
                    message TEXT,
                    match_type TEXT DEFAULT 'contains',
                    PRIMARY KEY (guild_id, name)
                )
            ''')
            await db.commit()

    @commands.group(name="autoresponder", invoke_without_command=True, aliases=['ar'], help="Manage autoresponders in the server.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _ar(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @_ar.command(name="create", help="Create a new autoresponder.")
    @commands.has_permissions(administrator=True)
    async def _create(self, ctx, name, *, message):
        name_lower = name.lower()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM autoresponses WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                count = (await cursor.fetchone())[0]
                if count >= 20:
                    return await ctx.reply(embed=discord.Embed(title="<:icon_cross:1381448030481547315> Error!",
                        description=f"You can't add more than 20 autoresponses in {ctx.guild.name}",
                        color=0x000000
                    ))

            async with db.execute("SELECT 1 FROM autoresponses WHERE guild_id = ? AND LOWER(name) = ?", (ctx.guild.id, name_lower)) as cursor:
                if await cursor.fetchone():
                    return await ctx.reply(embed=discord.Embed(title="<:icon_cross:1381448030481547315> Error!",
                        description=f"The autoresponse with the name `{name}` already exists in {ctx.guild.name}",
                        color=0x000000
                    ))

            await db.execute("INSERT INTO autoresponses (guild_id, name, message, match_type) VALUES (?, ?, ?, ?)", (ctx.guild.id, name_lower, message, "contains"))
            await db.commit()
            await ctx.reply(embed=discord.Embed(title="<:IconTick:1381245157759782975> Success",
                description=f"Created autoresponder `{name}` in {ctx.guild.name} with `contains` match type",
                color=0x000000
            ))

    @_ar.command(name="delete", help="Delete an existing autoresponder.")
    @commands.has_permissions(administrator=True)
    async def _delete(self, ctx, name):
        name_lower = name.lower()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT 1 FROM autoresponses WHERE guild_id = ? AND LOWER(name) = ?", (ctx.guild.id, name_lower)) as cursor:
                if not await cursor.fetchone():
                    return await ctx.reply(embed=discord.Embed(title="<:icon_cross:1381448030481547315> Error!",
                        description=f"No autoresponder found with the name `{name}` in {ctx.guild.name}",
                        color=0x000000
                    ))

            await db.execute("DELETE FROM autoresponses WHERE guild_id = ? AND LOWER(name) = ?", (ctx.guild.id, name_lower))
            await db.commit()
            await ctx.reply(embed=discord.Embed(title="<:IconTick:1381245157759782975> Success",
                description=f"Deleted autoresponder `{name}` in {ctx.guild.name}",
                color=0x000000
            ))

    @_ar.command(name="edit", help="Edit an existing autoresponder.")
    @commands.has_permissions(administrator=True)
    async def _edit(self, ctx, name, *, message):
        name_lower = name.lower()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT 1 FROM autoresponses WHERE guild_id = ? AND LOWER(name) = ?", (ctx.guild.id, name_lower)) as cursor:
                if not await cursor.fetchone():
                    return await ctx.reply(embed=discord.Embed(title="<:icon_cross:1381448030481547315> Error!",
                        description=f"No autoresponder found with the name `{name}` in {ctx.guild.name}",
                        color=0x000000
                    ))

            await db.execute("UPDATE autoresponses SET message = ? WHERE guild_id = ? AND LOWER(name) = ?", (message, ctx.guild.id, name_lower))
            await db.commit()
            await ctx.reply(embed=discord.Embed(title="<:IconTick:1381245157759782975> Success",
                description=f"Edited autoresponder `{name}` in {ctx.guild.name}",
                color=0x000000
            ))

    @_ar.command(name="matchtype", help="Set match type for an autoresponder: `exact` or `contains`.")
    @commands.has_permissions(administrator=True)
    async def _matchtype(self, ctx, name, mode: str):
        mode = mode.lower()
        if mode not in ["exact", "contains"]:
            return await ctx.reply(embed=discord.Embed(
                title="<:icon_cross:1381448030481547315> Invalid Match Type",
                description="Match type must be `exact` or `contains`.",
                color=0x000000
            ))

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE autoresponses SET match_type = ? WHERE guild_id = ? AND LOWER(name) = ?", (mode, ctx.guild.id, name.lower()))
            await db.commit()

        await ctx.reply(embed=discord.Embed(
            title="<:IconTick:1381245157759782975> Success",
            description=f"Updated match type of `{name}` to `{mode}`.",
            color=0x000000
        ))

    @_ar.command(name="config", help="List all autoresponders in the server.")
    @commands.has_permissions(administrator=True)
    async def _config(self, ctx):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT name, match_type FROM autoresponses WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                autoresponses = await cursor.fetchall()

        if not autoresponses:
            return await ctx.reply(embed=discord.Embed(
                description=f"<:icon_cross:1381448030481547315> | There are no autoresponders in {ctx.guild.name}",
                color=0x000000
            ))

        embed = discord.Embed(color=0x000000, title=f"Autoresponders in {ctx.guild.name}")
        for i, (name, match_type) in enumerate(autoresponses, start=1):
            embed.add_field(name=f"[{i}] `{name}`", value=f"Match Type: `{match_type}`", inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip().lower()

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT name, message, match_type FROM autoresponses WHERE guild_id = ?", (message.guild.id,)) as cursor:
                rows = await cursor.fetchall()

        for name, response_message, match_type in rows:
            if match_type == "exact" and content == name:
                return await message.channel.send(response_message)
            elif match_type == "contains" and name in content:
                return await message.channel.send(response_message)

async def setup(bot):
    await bot.add_cog(AutoResponder(bot))