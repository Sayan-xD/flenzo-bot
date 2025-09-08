
import discord
from discord.ext import commands

class Lock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="lock",
        help="Locks a channel to prevent sending messages.",
        usage="lock <channel>",
        aliases=["lockchannel"]
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock_command(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)

        # Already locked case
        if overwrite.send_messages is False:
            embed = discord.Embed(
                description=f"<a:olympus_WarnFlash:1380915318658174976> | {channel.mention} is already locked.",
                color=0xFFF700
            )
            embed.set_footer(text=f"", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return

        # Apply the lock
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)

        embed = discord.Embed(
            title="Successfully Locked!",
            description=f"<:IconTick:1381245157759782975> | {channel.mention} has been successfully locked.",
            color=0xFFF700
        )
        embed.set_footer(text=f"Locked by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Lock(bot))
