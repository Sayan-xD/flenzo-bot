
import discord
from discord.ext import commands
import asyncio
import json
import os

# Load purge config
if os.path.exists("autopurge_config.json"):
    with open("autopurge_config.json", "r") as f:
        autopurge_config = json.load(f)
else:
    autopurge_config = {}

class TimedTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.purge_tasks = {}

    @commands.command(name="timedrole")
    @commands.has_permissions(manage_roles=True)
    async def timedrole(self, ctx, member: discord.Member, role: discord.Role, duration: str):
        time_seconds = self.parse_duration(duration)
        if time_seconds is None:
            return await ctx.send("⚠️ Invalid time format. Use like `10m`, `2h`, `1d`.")

        await member.add_roles(role)
        await ctx.send(f"✅ {member.mention} got {role.mention} for {duration}")

        await asyncio.sleep(time_seconds)
        if role in member.roles:
            await member.remove_roles(role)
            try:
                await member.send(f"🔔 Your role {role.name} has expired in **{ctx.guild.name}**.")
            except:
                pass

    def parse_duration(self, duration):
        try:
            unit = duration[-1]
            value = int(duration[:-1])
            if unit == 'm':
                return value * 60
            elif unit == 'h':
                return value * 3600
            elif unit == 'd':
                return value * 86400
        except:
            return None

    @commands.command(name="autopurge")
    @commands.has_permissions(manage_messages=True)
    async def autopurge(self, ctx, channel: discord.TextChannel, delay: int):
        guild_id = str(ctx.guild.id)
        autopurge_config[guild_id] = {
            "channel_id": channel.id,
            "delay": delay
        }

        with open("autopurge_config.json", "w") as f:
            json.dump(autopurge_config, f, indent=4)

        await ctx.send(f"🧹 Messages in {channel.mention} will now auto-delete after {delay} minutes.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        if guild_id in autopurge_config:
            config = autopurge_config[guild_id]
            if message.channel.id == config["channel_id"]:
                delay = config["delay"]
                await asyncio.sleep(delay * 60)
                try:
                    await message.delete()
                except discord.NotFound:
                    pass

async def setup(bot):
    await bot.add_cog(TimedTools(bot))
