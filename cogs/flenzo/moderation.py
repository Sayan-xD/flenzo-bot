import discord
from discord.ext import commands


class sayan111111(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Moderation commands"""
  
    def help_custom(self):
		      emoji = '<:icon_moderation:1381159392384385116>'
		      label = "Moderation"
		      description = ""
		      return emoji, label, description

    @commands.group()
    async def __Moderation__(self, ctx: commands.Context):
        """`audit` , `warn` , `clearwarns` , `ban` , `clone` , `snipe` , `hide` , `hideall` , `kick` , `lock` , `mute` , `nick` , `nuke` , `role` , `roleicon` , `role all` , `role bots` , `role create` , `role delete` , `role humans` , `role rename` , `role temp` , `role unverified` , `slowmode` , `lockall` `unlockall` , `steal` , `unban` , `unhide` , `unhideall` , `unlock` , `unslowmode` , `removerole all` , `removerole bots` , `removerole humans` , `removerole unverified` , `clear` , `clear all` , `clear bots` , `clear contains` , `clear embeds` , `clear files` , `clear images` , `clear mentions` , `clear reactions` , `clear user` , `deleteemoji` , `deletesticker` , `enlarge`"""