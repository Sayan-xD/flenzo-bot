import discord
from discord.ext import commands

class OwnerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sin")
    @commands.is_owner()
    async def serverin(self, ctx, guild_id: int):
        """Get an invite link to a server by its ID (owner only)."""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return await ctx.send("❌ I’m not in a server with that ID.")

        invite_link = "❌ I couldn't create an invite."

        try:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).create_instant_invite:
                    invite = await channel.create_invite(max_age=0, max_uses=0, reason="Server invite requested by bot owner")
                    invite_link = invite.url
                    break
        except Exception as e:
            invite_link = f"⚠️ Error: `{e}`"

        try:
            await ctx.author.send(f"🔗 Invite to `{guild.name}`:\n{invite_link}")
            await ctx.send("✅ Sent the invite link in DMs!")
        except discord.Forbidden:
            await ctx.send("❌ I couldn't DM you. Please enable DMs from server members.")

async def setup(bot):
    await bot.add_cog(OwnerCommands(bot))