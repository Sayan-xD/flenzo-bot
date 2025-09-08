import discord
from discord.ext import commands

class ServerList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="slist", aliases=["serverlist"])
    @commands.is_owner()
    async def server_list(self, ctx):
        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)

        embeds = []
        per_page = 10
        for i in range(0, len(guilds), per_page):
            embed = discord.Embed(
                title=f"📋 Server List (Total: {len(guilds)})",
                color=discord.Color.blurple()
            )
            for j, guild in enumerate(guilds[i:i + per_page], start=i + 1):
                embed.add_field(
                    name=f"{j}. {guild.name}",
                    value=(
                        f"👥 Members: **{guild.member_count}**\n"
                        f"🆔 Guild ID: `{guild.id}`"
                    ),
                    inline=False
                )
            embed.set_footer(text=f"Page {i // per_page + 1} of {(len(guilds) - 1) // per_page + 1}")
            embeds.append(embed)

        if not embeds:
            await ctx.send("I'm not in any servers.")
        elif len(embeds) == 1:
            await ctx.send(embed=embeds[0])
        else:
            await ctx.send(embed=embeds[0], view=ServerListView(embeds))

    @commands.command(name="lsv", aliases=["leaveserver"])
    @commands.is_owner()
    async def leave_server(self, ctx, guild_id: int):
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"❌ I couldn't find a server with ID `{guild_id}`.",
                    color=discord.Color.red()
                )
            )

        try:
            await guild.leave()
            await ctx.send(
                embed=discord.Embed(
                    title="👋 Left Server",
                    description=f"Successfully left **{guild.name}** (`{guild.id}`)",
                    color=discord.Color.green()
                )
            )
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="❌ Failed to Leave",
                    description=f"An error occurred: `{str(e)}`",
                    color=discord.Color.red()
                )
            )


async def setup(bot):
    await bot.add_cog(ServerList(bot))