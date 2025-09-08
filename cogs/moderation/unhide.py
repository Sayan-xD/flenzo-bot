
import discord
from discord.ext import commands

class Unhide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="unhide",
        help="Unhides a channel for @everyone.",
        usage="unhide <channel>",
        aliases=["unhidechannel"]
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unhide_command(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)

        # Already visible
        if overwrite.view_channel is None or overwrite.view_channel is True:
            embed = discord.Embed(
                description=f"<a:olympus_WarnFlash:1380915318658174976> | {channel.mention} is already visible.",
                color=0xFFF700  # Lightning yellow
            )
            embed.set_footer(text=f"", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return

        # Unhide the channel
        await channel.set_permissions(ctx.guild.default_role, view_channel=True)

        embed = discord.Embed(
            title="Successfully Unhidden!",
            description=f"<:IconTick:1381245157759782975> | {channel.mention} has been successfully unhidden.",
            color=0xFFF700  # Lightning yellow
        )
        embed.set_footer(text=f"Unhidden by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Unhide(bot))
