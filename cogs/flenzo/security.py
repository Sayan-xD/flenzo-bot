import discord
from discord.ext import commands


class sayan1(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Security commands"""
  
    def help_custom(self):
		      emoji = '<:security:1381152589340479589>'
		      label = "Security"
		      description = ""
		      return emoji, label, description

    @commands.group()
    async def __Security__(self, ctx: commands.Context):
        """`antinuke` , `antinuke enable` , `antinuke disable` , `whitelist` , `whitelist @user` , `unwhitelist` , `whitelisted` , `whitelist reset` , `extraowner` , `extraowner set` , `extraowner view` , `extraowner reset`, `nightmode` , `nightmode enable` , `nightmode disable`"""

