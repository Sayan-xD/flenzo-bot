import discord
from discord.ext import commands


class fastgreet(commands.Cog, name="Fastgreet"):
    def __init__(self, bot):
        self.bot = bot

    """Fastgreet Commands"""
  
    def help_custom(self):
		      emoji = '<:Greet:1399559983498002522>'
		      label = "Fastgreet"
		      description = "Give A Welcome Message And Delete It Under 2s"
		      return emoji, label, description

    @commands.group()
    async def __Fastgreet__(self, ctx: commands.Context):
        """`fastgreet` , `fastgreet enable` , `fastgreet disable` , `fastgreet list` , `fastgreet setmessage` , `fastgreet test` , `fastgreet variables`"""