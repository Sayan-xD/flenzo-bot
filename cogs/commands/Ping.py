import os 
import discord
from discord.ext import commands
import datetime
import sys
from discord.ui import Button, View
import psutil
import time
from utils.Tools import *
from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown
import requests
from typing import *
from utils import *
from utils.config import BotName, serverLink
from utils import Paginator, DescriptionEmbedPaginator, FieldPagePaginator, TextPaginator
from core import Cog, Flenzo, Context
from typing import Optional
import aiosqlite 
import asyncio
import aiohttp


class PingView(View):
    def __init__(self, provider, author_id):
        super().__init__(timeout=30)
        self.provider = provider
        self.author_id = author_id

    @discord.ui.button(label="Provider", style=discord.ButtonStyle.grey)
    async def show_provider(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message(
                "⚠️ This button is only for the one who used the command.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="🔧 Bot Hosting Provider",
            description=f"**🌐 Our hosting is proudly powered by [HeavenHQ](https://discord.gg/heavenhq) 💠**.",
            color=0x2F3136
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x000000

    @commands.hybrid_command(
        name="ping",
        aliases=["latency"],
        help="Check the bot and database latency.",
        description="Check the bot and database latency."
    )
    @commands.cooldown(1, 2, commands.BucketType.user)
    @blacklist_check()
    @ignore_check()
    async def ping(self, ctx):
        bot_latency = round(self.bot.latency * 1000, 2)

        try:
            async with aiosqlite.connect("db/afk.db") as db:
                start = time.perf_counter()
                await db.execute("SELECT 1")
                end = time.perf_counter()
                db_latency = round((end - start) * 1000, 2)
        except Exception:
            db_latency = "N/A"

        embed = discord.Embed(
            title="🏓 Pong!",
            color=self.color
        )
        embed.add_field(name="**Bot Latency**", value=f"🛰️ `{bot_latency}ms`", inline=True)
        embed.add_field(name="**Database Latency**", value=f"🗄️ `{db_latency}ms`", inline=True)
        embed.set_footer(
            text=f"Requested by {ctx.author}",
            icon_url=ctx.author.display_avatar.url
        )
        embed.timestamp = discord.utils.utcnow()

        provider = ""  # Change this to your actual hosting provider
        view = PingView(provider=provider, author_id=ctx.author.id)

        await ctx.send(embed=embed, view=view)


# Don't forget setup function if you're using cogs
async def setup(bot):
    await bot.add_cog(Ping(bot))