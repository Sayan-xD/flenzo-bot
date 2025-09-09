import discord
from discord.ext import commands


class sayan11111111111111(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Welcome commands"""
  
    def help_custom(self):
		      emoji = '<:icon_welcome:1381153974144466985>'
		      label = "Welcomer"
		      description = ""
		      return emoji, label, description

    @commands.group()
    async def __Welcomer__(self, ctx: commands.Context):
        """`autorole` , `autorole bots add` , `autorole bots remove` , `autorole bots` , `autorole config` , `autorole humans add` , `autorole humans remove` , `autorole humans` , `autorole reset all` , `autorole reset bots` , `autorole reset humans` , `greet setup` , `greet reset`, `greet channel` , `greet edit` , `greet test` , `greet config` , `greet autodeletete` , `greet` , `joindm` , `joindm message` , `joindm variables` , ` joindm delete` , `joindm config` , `joindm test`"""