
import discord
from discord.ext import commands
from discord import app_commands

class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Prefix command
    @commands.command(name="vote", aliases=["votelink"])
    async def vote_cmd(self, ctx):
        await self.send_vote(ctx)

    # Slash command
    @app_commands.command(name="vote", description="Vote for the bot on Top.gg")
    async def vote_slash(self, interaction: discord.Interaction):
        await self.send_vote(interaction)

    async def send_vote(self, ctx_or_interaction):
        vote_url = "https://top.gg/bot/998547879201349693/vote"

        embed = discord.Embed(
            description="🤖 | [Click here to vote me.](%s)" % vote_url,
            color=discord.Color.dark_teal()
        )

        view = discord.ui.View()
        button = discord.ui.Button(
            label="Vote", url=vote_url,
            emoji="🔗", style=discord.ButtonStyle.link
        )
        view.add_item(button)

        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed, view=view)
        else:
            await ctx_or_interaction.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Vote(bot))
