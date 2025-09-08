import discord
from discord.ext import commands
import sqlite3

class ForcePrefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "db/prefix.db"

    def update_prefix(self, guild_id: int, prefix: str):
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "REPLACE INTO prefixes (guild_id, prefix) VALUES (?, ?)",
                (guild_id, prefix),
            )

    def remove_prefix(self, guild_id: int):
        with sqlite3.connect(self.db_path) as db:
            db.execute("DELETE FROM prefixes WHERE guild_id = ?", (guild_id,))

    @commands.command(name="forceprefix", aliases=["fprefix"])
    @commands.is_owner()
    async def forceprefix(self, ctx, new_prefix: str):
        """Change the bot's prefix in this server (Bot owner only)."""
        self.update_prefix(ctx.guild.id, new_prefix)
        embed = discord.Embed(
            title="🔧 Force Prefix Updated",
            description=f"Prefix for **{ctx.guild.name}** is now set to `{new_prefix}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="resetprefix")
    @commands.is_owner()
    async def resetprefix(self, ctx):
        """Reset the prefix for this server to default (Bot owner only)."""
        self.remove_prefix(ctx.guild.id)
        embed = discord.Embed(
            title="♻️ Prefix Reset",
            description=f"Prefix for **{ctx.guild.name}** has been reset to default.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @forceprefix.error
    @resetprefix.error
    async def prefix_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("🚫 Only the **bot owner** can use this command.")

def setup(bot):
    bot.add_cog(ForcePrefix(bot))