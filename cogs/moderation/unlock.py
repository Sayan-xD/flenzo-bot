
import discord
from discord.ext import commands

class Unlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="unlock",
        help="Unlocks a channel to allow sending messages.",
        usage="unlock <channel>",
        aliases=["unlockchannel"]
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock_command(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)

        # Already unlocked case
        if overwrite.send_messages is None or overwrite.send_messages is True:
            embed = discord.Embed(
                description=f"<a:olympus_WarnFlash:1380915318658174976> | {channel.mention} is already unlocked.",
                color=0xFFF700
            )
            embed.set_footer(text=f"", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return

        # Remove lock
        await channel.set_permissions(ctx.guild.default_role, send_messages=True)

        embed = discord.Embed(
            title="Successfully Unlocked!",
            description=f"<:IconTick:1381245157759782975> | {channel.mention} has been successfully unlocked.",
            color=0xFFF700
        )
        embed.set_footer(text=f"Unlocked by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Unlock(bot))
