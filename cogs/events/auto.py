import discord
from discord.utils import *
from core import Flenzo, Cog
from utils.Tools import *
from utils.config import BotName, serverLink
from discord.ext import commands
from discord.ui import Button, View

class Autorole(Cog):
    def __init__(self, bot: Flenzo):
        self.bot = bot


    @commands.Cog.listener(name="on_guild_join")
    async def send_msg_to_adder(self, guild: discord.Guild):
        async for entry in guild.audit_logs(limit=3):
            if entry.action == discord.AuditLogAction.bot_add:
                embed = discord.Embed(
                    description=f"<:Icon_Mail:1381572449614823425>  **Thanks for adding me.**\n\n<a:bullet:1383648817483747348> My default prefix is `?`\n<a:bullet:1383648817483747348> Use the `?help` command to see a list of commands\n<a:bullet:1383648817483747348> For detailed guides, FAQ and information, visit our **[Support Server](https://discord.gg/C86nD33WBr)**",
                    color=0xff0000
                )
                embed.set_thumbnail(url=entry.user.avatar.url if entry.user.avatar else entry.user.default_avatar.url)
                embed.set_author(name=f"{guild.name}", icon_url=guild.me.display_avatar.url)
                embed.set_footer(text="Powered by Flenzo Development", icon_url="https://cdn.discordapp.com/avatars/998547879201349693/c7c8f9a3105ed25d22b2535c3b407fa8.png?size=1024")
                support_button = Button(label='Support', style=discord.ButtonStyle.link, url='https://dsc.gg/flenzobot')
                view = View()
                view.add_item(support_button)
                
                #view.add_item(vote_button)
                if guild.icon:
                    embed.set_author(name=guild.name, icon_url=guild.icon.url)
                try:
                    await entry.user.send(embed=embed, view=view)
                except Exception as e:
                    print(e)
