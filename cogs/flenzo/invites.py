import discord
from discord.ext import commands


class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """InviteTracker commands"""

    def help_custom(self):
              emoji = '<:Vanity_Roles:1383631102887067688>'
              label = "InviteTracker"
              description = ""
              return emoji, label, description

    @commands.group()
    async def __InviteTracker__(self, ctx: commands.Context):
        """`invites`, `inviter`, `invited`, `resetinvites`, `resetinvitesall`, `resetmyinvites`, `invlb`"""