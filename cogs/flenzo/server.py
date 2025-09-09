import discord
from discord.ext import commands

class sayan11111111111(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Server commands"""
  
    def help_custom(self):
		      emoji = '<:kylo_module:1381162575244296213>'
		      label = "Server"
		      description = ""
		      return emoji, label, description

    @commands.group()
    async def __Setup__(self, ctx: commands.Context):
        """`setup` , `setup create <name>` , `setup delete <name>`  , `setup list` , `setup staff` , `setup girl` , `setup friend` , `setup vip` , `setup guest` , `setup config` , `setup reset` , `staff` , `girl` , `friend` , `vip` , `guest` , `autoresponder` , `autoresponder create` , `autoresponder delete` , `autoresponder edit` , `autoresponder config` , `react` , `react add` , `react remove` , `react list` , `react reset`"""

