import discord
from discord.ext import commands
import asyncio

class React(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        for owner in self.bot.owner_ids:
            if f"<@{owner}>" in message.content:
                try:
                    if owner == 833509477754994698:
                        
                        emojis = [
                            "<:MekoDeveloper:1392139514235064435>"
                            
  
                        ]
                        for emoji in emojis:
                            await message.add_reaction(emoji)
                    else:
                        
                        await message.add_reaction("<:gold_owner:1389297086704521226>")
                except discord.errors.RateLimited as e:
                    await asyncio.sleep(e.retry_after)
                    await message.add_reaction("<:gold_owner:1389297086704521226>")
                except Exception as e:
                    print(f"An unexpected error occurred Auto react owner mention: {e}")
