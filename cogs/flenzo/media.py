import discord
from discord.ext import commands


class sayanMedia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Vanity Roles"""

    def help_custom(self):
              emoji = '<:ather_vanityrole:1398108434859294809>'
              label = "Vanity Roles"
              description = ""
              return emoji, label, description

    @commands.group()
    async def __VanityRoles__(self, ctx: commands.Context):
        """`vanityroles setup`, `vanityroles reset`, `vanityroles show`"""