import discord
from discord.ext import commands
import wavelink
import os
import json

class VC247(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.file = "db/247.json"
        self.data = self.load_data()
        self.bot.loop.create_task(self.join_vcs_on_ready())

    def load_data(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.file):
            with open(self.file, "w") as f:
                json.dump({}, f)
        with open(self.file, "r") as f:
            return json.load(f)

    def save_data(self):
        with open(self.file, "w") as f:
            json.dump(self.data, f, indent=4)

    @commands.hybrid_command(name="247", help="Toggle 24/7 VC mode", usage="247")
    @commands.has_permissions(administrator=True)
    async def _247(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send(embed=discord.Embed(
                description="<:icon_cross:1381448030481547315> | You must be connected to a voice channel.",
                color=0xFF0000
            ))

        guild_id = str(ctx.guild.id)
        user_vc = ctx.author.voice.channel

        if guild_id in self.data:
            saved_vc = self.data[guild_id]["channel_id"]
            if saved_vc != user_vc.id:
                return await ctx.send(embed=discord.Embed(
                    description="<:icon_cross:1381448030481547315> | You must be in the **same VC** where 24/7 is enabled to disable it.",
                    color=0xFF0000
                ))

            # Disable 24/7
            del self.data[guild_id]
            self.save_data()

            if ctx.voice_client:
                await ctx.voice_client.disconnect(force=True)

            return await ctx.send(embed=discord.Embed(
                description="<:IconTick:1381245157759782975> | **24/7 Mode** is now **disabled**.",
                color=0xFF0000
            ))

        # Enable 24/7
        self.data[guild_id] = {"channel_id": user_vc.id}
        self.save_data()

        if not ctx.voice_client:
            await user_vc.connect(cls=wavelink.Player)

        await ctx.send(embed=discord.Embed(
            description="<:IconTick:1381245157759782975> | **24/7 Mode** is now **enabled**.",
            color=0x1DB954
        ))

    async def join_vcs_on_ready(self):
        await self.bot.wait_until_ready()
        for guild_id, info in self.data.items():
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            channel = guild.get_channel(info["channel_id"])
            if channel:
                try:
                    await channel.connect(cls=wavelink.Player)
                    print(f"[247] Rejoined VC in {guild.name}")
                except Exception as e:
                    print(f"[247] Failed to rejoin in {guild.name}: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id != self.bot.user.id:
            return

        guild_id = str(member.guild.id)
        data = self.data.get(guild_id)
        if not data:
            return

        # Bot disconnected
        if before.channel and not after.channel:
            vc = member.guild.get_channel(data["channel_id"])
            if vc:
                try:
                    await vc.connect(cls=wavelink.Player)
                except:
                    pass

        # Bot moved to wrong VC
        elif after.channel and after.channel.id != data["channel_id"]:
            correct_vc = member.guild.get_channel(data["channel_id"])
            if correct_vc:
                try:
                    await correct_vc.connect(cls=wavelink.Player)
                except:
                    pass

def setup(bot):
    bot.add_cog(VC247(bot))