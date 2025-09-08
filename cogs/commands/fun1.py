import discord
from discord.ext import commands
import random

class Fun1(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rate")
    async def rate(self, ctx, *, thing: str):
        rating = random.randint(0, 10)
        await ctx.send(f"I'd rate **{thing}** a solid **{rating}/10**!")

    @commands.command(name="flip")
    async def flip(self, ctx):
        result = random.choice(["Heads", "Tails"])
        await ctx.send(f"🪙 The coin landed on **{result}**!")

    @commands.command(name="roast")
    async def roast(self, ctx, member: discord.Member = None):
        roasts = [
            "You're as useless as the 'g' in lasagna.",
            "If I had a dollar for every smart thing you said, I'd be broke.",
            "You're the reason shampoo has instructions.",
            "You're like a cloud. When you disappear, it's a beautiful day.",
            "You're proof that even evolution can take a break."
        ]
        if member is None:
            member = ctx.author
        roast = random.choice(roasts)
        await ctx.send(f"{member.mention}, {roast}")

async def setup(bot):
    await bot.add_cog(Fun1(bot))
