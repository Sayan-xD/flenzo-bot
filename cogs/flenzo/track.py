import discord
from discord.ext import commands

class sayanTrack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Uptime Logging"""
  
    def help_custom(self):
		      emoji = '<:MekoInvestor:1401071657044541490>'
		      label = "Uptime Logging"
		      description = ""
		      return emoji, label, description

    @commands.group()
    async def __UptimeLogging__(self, ctx: commands.Context):
        """`track add` , `track delete` , `track config` , `track stats` , `track clear` , `track """