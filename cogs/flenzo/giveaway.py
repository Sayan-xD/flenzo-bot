import discord
from discord.ext import commands


class sayan11111111111111111(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Giveaway commands"""
  
    def help_custom(self):
		      emoji = '<:icon_GiveawayIcon:1401073685921529927>'
		      label = "Giveaway"
		      description = ""
		      return emoji, label, description

    @commands.group()
    async def __Giveaway__(self, ctx: commands.Context):
        """`gstart`, `gend`, `greroll` , `glist`"""