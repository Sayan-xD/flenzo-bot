import discord
from discord.ext import commands


class Loggingdrop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Logging commands"""

    def help_custom(self):
              emoji = '<:logging_icons:1383631811099361333>'
              label = "Logging"
              description = ""
              return emoji, label, description

    @commands.group()
    async def __Logging__(self, ctx: commands.Context):
        """`logging`, `logging setup`, `logging status`, `logging reset`"""