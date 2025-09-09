import discord
from discord.ext import commands


class vcrole66(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Tracking Command"""

    def help_custom(self):
              emoji = '<:icons_plus:1381456773554114623>'
              label = "Tracking Commands"
              description = ""
              return emoji, label, description

    @commands.group()
    async def __Tracking__(self, ctx: commands.Context):
        """`invites` , `resetinvites` , `resetinvitesall`"""