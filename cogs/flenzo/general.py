import discord
from discord.ext import commands


class sayan111(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """General commands"""

    def help_custom(self):
              emoji = '<:rn_server:1383629029768171632>'
              label = "General"
              description = ""
              return emoji, label, description

    @commands.group()
    async def __General__(self, ctx: commands.Context):
        """`status` , `afk` , `avatar` , `banner` , `servericon` , `membercount` , `poll` , `hack` , `token` , `users` , `wizz` , `urban` , `rickroll` , `hash` , `snipe` , `users` , `list boosters` , `list inrole` , `list emojis` , `list bots` , `list admins` , `list invoice` , `list mods` , `list early` , `list activedeveloper` , `list createpos` , `list roles`"""