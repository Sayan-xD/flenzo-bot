import discord
from discord.ext import commands


class sayanMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Music commands"""

    def help_custom(self):
              emoji = '<:icons_Music:1381153136080719913>'
              label = "Music"
              description = ""
              return emoji, label, description

    @commands.group()
    async def __Music__(self, ctx: commands.Context):
        """`247` , `play` , `search` , `loop` , `autoplay` , `nowplaying` , `shuffle` , `stop` , `skip` , `seek` , `join` , `disconnect` , `replay` , `queue` , `clearqueue` , `pause` , `resume` , `volume` , `filter` , `filter enable` , `filter disable`"""