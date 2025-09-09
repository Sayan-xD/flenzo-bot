import discord
from discord.ext import commands


class sayanIgnore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Ignore commands"""

    def help_custom(self):
              emoji = '<:ignore:1383629979644071949>'
              label = "Ignore"
              description = ""
              return emoji, label, description

    @commands.group()
    async def __Ignore__(self, ctx: commands.Context):
        """`ignore` , `ignore command add` , `ignore command remove` , `ignore command show` , `ignore channel add` , `ignore channel remove` , `ignore channel show` , `ignore user add` , `ignore user remove` , `ignore user show` , `ignore bypass add` , `ignore bypass show` , `ignore bypass remove`"""