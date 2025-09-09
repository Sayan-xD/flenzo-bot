import discord
from discord.ext import commands


class Vanityroles69999(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Birthday Commands"""

    def help_custom(self):
              emoji = '<:Vanity_Roles:1383631102887067688>'
              label = "Birthday"
              description = ""
              return emoji, label, description

    @commands.group()
    async def __Birthday__(self, ctx: commands.Context):
        """`setbirthday`, `birthday`, `nextbirthdays`, `deletebirthday`, `birthdayrole`, `birthdays`"""