import discord
import psutil
import sys
import os
import time
import aiosqlite
import platform
import datetime
from discord import Embed, ButtonStyle
from discord.ui import Button, View
from discord.ext import commands
import wavelink

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.total_songs_played = 0
        self.bot.loop.create_task(self.setup_database())

    async def setup_database(self):
        async with aiosqlite.connect("db/stats.db") as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value INTEGER
            )""")
            await db.commit()

            async with db.execute("SELECT value FROM stats WHERE key = 'total_songs_played'") as cursor:
                row = await cursor.fetchone()
                self.total_songs_played = row[0] if row else 0

    async def update_total_songs_played(self):
        async with aiosqlite.connect("db/stats.db") as db:
            await db.execute("INSERT OR REPLACE INTO stats (key, value) VALUES ('total_songs_played', ?)", (self.total_songs_played,))
            await db.commit()

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        self.total_songs_played += 1
        await self.update_total_songs_played()

    @commands.hybrid_command(name="stats", aliases=["botinfo", "botstats", "bi", "statistics"], help="Shows the bot's information.")
    async def stats(self, ctx):
        processing_message = await ctx.send("<a:Loading:1381163276439781476> Loading information...")

        # Basic stats
        guild_count = len(self.bot.guilds)
        user_count = sum(g.member_count or 0 for g in self.bot.guilds)
        bot_count = sum(sum(1 for m in g.members if m.bot) for g in self.bot.guilds)
        human_count = user_count - bot_count
        uptime = str(datetime.timedelta(seconds=int(round(time.time() - self.start_time))))
        latency = f"{int(self.bot.latency * 1000)}ms"
        shard_count = len(self.bot.shards)
        commands_count = len(set(self.bot.walk_commands()))
        slash_commands = len(self.bot.tree.get_commands())

        embed = Embed(title="Flenzo's Statistics: General", color=0x000000)
        embed.add_field(
            name="- System Information",
            value=(
                f"> Server Count: `{guild_count}`\n"
                f"> User Count: `{user_count}`\n"
                f"> Total Commands: `{commands_count}`\n"
                f"> App Commands: `{slash_commands}`\n"
                f"> Shard Count: `{shard_count}`\n"
                f"> Uptime: `{uptime}`\n"
                f"> Latency: `{latency}`"
            ),
            inline=False
        )
        embed.set_footer(text="Thanks For Using Flenzo", icon_url=self.bot.user.display_avatar.url)

        view = View()

        # GENERAL BUTTON
        general_button = Button(label="General", style=ButtonStyle.gray)
        async def general_button_callback(interaction):
            if interaction.user == ctx.author:
                await interaction.response.edit_message(embed=embed, view=view)
        general_button.callback = general_button_callback
        view.add_item(general_button)

        # SYSTEM BUTTON
        system_button = Button(label="System", style=ButtonStyle.grey)
        async def system_button_callback(interaction):
            if interaction.user != ctx.author:
                return await interaction.response.send_message("❌ Only command author can use this.", ephemeral=True)

            db_latency = "N/A"
            try:
                async with aiosqlite.connect("db/afk.db") as db:
                    start = time.perf_counter()
                    await db.execute("SELECT 1")
                    end = time.perf_counter()
                    db_latency = round((end - start) * 1000, 2)
            except:
                pass

            ram = psutil.virtual_memory()
            sys_embed = Embed(title="Flenzo's Statistic: System", color=0x000000)
            sys_embed.add_field(
                name="- System Stats",
                value=(
                    f"> CPU Usage: `{psutil.cpu_percent()}%`\n"
                    f"> RAM Usage: `{ram.percent}%`\n"
                    f"> Used Memory: `{int((ram.total - ram.available) / 1024 / 1024)} MB`\n"
                    f"> Disk Usage: `{psutil.disk_usage('/').percent}%`\n"
                    f"> Python: `{sys.version_info.major}.{sys.version_info.minor}`\n"
                    f"> discord.py: `{discord.__version__}`\n"
                    f"> DB Ping: `{db_latency}ms`"
                ),
                inline=False
            )
            sys_embed.set_footer(text="Flenzo on Top?", icon_url=self.bot.user.display_avatar.url)
            await interaction.response.edit_message(embed=sys_embed, view=view)
        system_button.callback = system_button_callback
        view.add_item(system_button)

        # ABOUT BUTTON
        about_button = Button(label="About", style=ButtonStyle.grey)
        async def about_button_callback(interaction):
            if interaction.user != ctx.author:
                return await interaction.response.send_message("❌ Only command author can use this.", ephemeral=True)

            dev_ids = [833509477754994698]  # Add more if needed
            owner_ids = [388289231455256578]  # Add more if needed

            def get_status_emoji(member):
                if not member:
                    return "**<:icons_offline:1381454822946897991> Offline**"
                status = member.status
                if status == discord.Status.online:
                    return "**<:icons_online:1381454833873191033> Online**"
                elif status == discord.Status.idle:
                    return "**<:LM_Icons_Idle:1381454816596983909> Idle**"
                elif status == discord.Status.dnd:
                    return "**<:Icon_Dnd:1381454870770487338> DND**"
                else:
                    return "**<:icons_offline:1381454822946897991> Offline**"

            dev_lines = [f"<@{uid}> - {get_status_emoji(ctx.guild.get_member(uid))}" for uid in dev_ids]
            owner_lines = [f"<@{uid}> - {get_status_emoji(ctx.guild.get_member(uid))}" for uid in owner_ids]

            team_embed = Embed(title="Flenzo's Team", color=0x000000)
            team_embed.add_field(
                name="**<:MekoDeveloper:1392139514235064435> Bot Developer(s)**",
                value="\n".join(dev_lines),
                inline=False
            )
            team_embed.add_field(
                name="**<:gold_owner:1389297086704521226> Bot Owner(s)**",
                value="\n".join(owner_lines),
                inline=False
            )
            team_embed.add_field(
                name="Links",
                value="**🔧 Host:** https://discord.gg/heavenhq\n**🎟️ Support:** https://discord.gg/C86nD33WBr",
                inline=False
            )
            team_embed.set_footer(text="Flenzo's Team", icon_url=self.bot.user.display_avatar.url)
            await interaction.response.edit_message(embed=team_embed, view=view)
        about_button.callback = about_button_callback
        view.add_item(about_button)

        await ctx.reply(embed=embed, view=view)
        await processing_message.delete()

async def setup(bot):
    await bot.add_cog(Stats(bot))