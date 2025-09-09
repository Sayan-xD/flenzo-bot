import discord
from discord.ext import commands


class sayanticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Ticket commands"""

    def help_custom(self):
              emoji = '<:nt_ticket:1401071833901699143>'
              label = "Ticket"
              description = ""
              return emoji, label, description

    @commands.group()
    async def __Ticket__(self, ctx: commands.Context):
        """`ticket create` , `ticket reopen` , `ticket delete (for delete the panel)` , `ticket create` , `ticket info`"""