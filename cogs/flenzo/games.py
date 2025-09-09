import discord
from discord.ext import commands

class sayan1111111111(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Games commands"""
  
    def help_custom(self):
		      emoji = '<:rn_automod:1383630789337546782>'
		      label = "Games"
		      description = ""
		      return emoji, label, description

    @commands.group()
    async def __Games__(self, ctx: commands.Context):
        """`blackjack` , `chess` , `tic-tac-toe` , `country-guesser` , `rps` , `lights-out` , `wordle` , `2048` , `memory-game` , `number-slider` , `battleship` , `connect-four` , `slots` , `dungeon`, `dungeon start` , `dungeon go left` , `dungeon go right` , `dungeon fight` , `dungeon run`"""