from utils import getConfig  
import discord
from discord.ext import commands
from utils.Tools import get_ignore_data
import aiosqlite

class Mention(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.color = 0xdc143c
        self.bot_name = "Flenzo"

    async def is_blacklisted(self, message):
        async with aiosqlite.connect("db/block.db") as db:
            cursor = await db.execute("SELECT 1 FROM guild_blacklist WHERE guild_id = ?", (message.guild.id,))
            if await cursor.fetchone():
                return True
                
            cursor = await db.execute("SELECT 1 FROM user_blacklist WHERE user_id = ?", (message.author.id,))
            if await cursor.fetchone():
                return True

        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if await self.is_blacklisted(message):
            return

        ignore_data = await get_ignore_data(message.guild.id)
        if str(message.author.id) in ignore_data["user"] or str(message.channel.id) in ignore_data["channel"]:
            return

        if message.reference and message.reference.resolved:
            if isinstance(message.reference.resolved, discord.Message):
                if message.reference.resolved.author.id == self.bot.user.id:
                    return

        guild_id = message.guild.id
        data = await getConfig(guild_id) 
        prefix = data["prefix"]

        if self.bot.user in message.mentions:
            if len(message.content.strip().split()) == 1:
                embed = discord.Embed(
                    title='<a:iconodiamante:1381319372605362399> Flenzo Here!',
                    color=self.color,
                    description=f"""Hey! I’m **[Flenzo](https://discord.com/oauth2/authorize?client_id=998547879201349693)** — a powerful multipurpose bot with **Security**, **AutoMod**, **Giveaways**, and more!\n
**[Support](https://discord.gg/C86nD33WBr) | [Invite Me](https://discord.com/oauth2/authorize?client_id=998547879201349693)**\n
**<a:bullet:1383648817483747348> My Prefix: `{prefix}`
<a:bullet:1383648817483747348> Commands: `{len(set(self.bot.walk_commands()))}`
<a:bullet:1383648817483747348> Try `{prefix}help` to explore!**""",
                )
                embed.set_thumbnail(url=self.bot.user.avatar.url)
                embed.set_footer(text="Powered by Flenzo", icon_url=self.bot.user.avatar.url)

                

                await message.channel.send(embed=embed)
                
async def setup(bot):
    await bot.add_cog(Mention(bot))