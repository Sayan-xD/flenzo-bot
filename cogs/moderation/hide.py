
import discord
from discord.ext import commands

class Hide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="hide",
        help="Hides a channel from @everyone.",
        usage="hide <channel>",
        aliases=["hidechannel"]
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def hide_command(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)

        # Already hidden
        if overwrite.view_channel is False:
            embed = discord.Embed(
                description=f"<a:olympus_WarnFlash:1380915318658174976> | {channel.mention} is already hidden.",
                color=0xFFF700
            )
            embed.set_footer(text=f"Hidden by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return

        # Hide the channel
        await channel.set_permissions(ctx.guild.default_role, view_channel=False)

        embed = discord.Embed(
            title="Successfully Hidden!",
            description=f"<:IconTick:1381245157759782975> | {channel.mention} has been successfully hidden.",
            color=0xFFF700
        )
        embed.set_footer(text=f"Hidden by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Hide(bot))
