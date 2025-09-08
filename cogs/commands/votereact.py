
import discord
from discord.ext import commands
import json
import os

# Load or create config
if os.path.exists("vote_config.json"):
    with open("vote_config.json", "r") as f:
        vote_config = json.load(f)
else:
    vote_config = {}

class VoteReact(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setupvotechannel")
    @commands.has_permissions(administrator=True)
    async def setupvotechannel(self, ctx, channel: discord.TextChannel, upvote: str):
        guild_id = str(ctx.guild.id)

        vote_config[guild_id] = {
            "channel_id": channel.id,
            "upvote": upvote
        }

        with open("vote_config.json", "w") as f:
            json.dump(vote_config, f, indent=4)

        await ctx.send(f"✅ Voting set in {channel.mention} with reaction: {upvote}")

    @commands.command(name="disablevotechannel")
    @commands.has_permissions(administrator=True)
    async def disablevotechannel(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in vote_config:
            del vote_config[guild_id]
            with open("vote_config.json", "w") as f:
                json.dump(vote_config, f, indent=4)
            await ctx.send("❌ Voting reaction feature has been disabled.")
        else:
            await ctx.send("⚠️ Voting feature is not set up for this server.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return

        guild_id = str(message.guild.id)
        if guild_id in vote_config:
            setup = vote_config[guild_id]
            if message.channel.id == setup["channel_id"]:
                try:
                    await message.add_reaction(setup["upvote"])
                except discord.HTTPException:
                    pass  # Ignore emoji errors

async def setup(bot):
    await bot.add_cog(VoteReact(bot))
