import discord
from discord.ext import commands


class sayan111111111(commands.Cog, name="Fun+"):
    def __init__(self, bot):
        self.bot = bot

    """Fun commands"""
  
    def help_custom(self):
		      emoji = '<:icons_games:1381156209381343312>'
		      label = "Fun"
		      description = ""
		      return emoji, label, description

    @commands.group()
    async def __Fun__(self, ctx: commands.Context):
        """`/imagine(slash)` , `mydog` , `chat` , `translate` , `howgay` , `lesbian` , `cute` , `intelligence`, `chutiya` , `horny` , `tharki` , `gif` , `iplookup` , `weather` , `hug` , `kiss` , `pat` , `cuddle` , `slap` , `tickle` , `spank` , `ngif` , `8ball` , `truth` , `dare` , `rate` , `flip` , `roast`"""