import discord
from discord.ext import commands


class sayan11(commands.Cog, name="Utility"):
    def __init__(self, bot):
        self.bot = bot

    """Utility commands"""
  
    def help_custom(self):
		      emoji = '<:Utility:1381152992052645890>'
		      label = "Utility"
		      description = ""
		      return emoji, label, description

    @commands.group()
    async def __Utility__(self, ctx: commands.Context):
        """`botinfo` , `stats` , `invite` , `serverinfo` , `userinfo` , `roleinfo` , `boostcount` , `unbanall` ,  `joined-at` , `ping` , `github` , `vcinfo` , `channelinfo` , `badges` , `banner user` , `banner server` , `reminder start` , `reminder clear` , `permissions` , `timer`"""