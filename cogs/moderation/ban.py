import discord
from discord.ext import commands
from discord import ui

class ConfirmBanView(ui.View):
    def __init__(self, ctx, member, reason):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.member = member
        self.reason = reason

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("You are not allowed to interact with this.", ephemeral=True)
            return False
        return True

    @ui.button(label="Confirm", style=discord.ButtonStyle.success, emoji="<:IconTick:1381245157759782975>")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            try:
                dm_embed = discord.Embed(
                    title="🚫 You have been banned",
                    description=f"You were banned from **{self.ctx.guild.name}** by {self.ctx.author} for **{self.reason}**",
                    color=0xFFF700
                )
                await self.member.send(embed=dm_embed)
            except:
                pass

            await self.member.ban(reason=self.reason)

            embed = discord.Embed(
                title="<:IconTick:1381245157759782975> Member Banned",
                description=f"{self.member.mention} has been banned by {self.ctx.author} for {self.reason}",
                color=0xFFF700
            )
            embed.set_footer(text=f"Banned by {self.ctx.author}", icon_url=self.ctx.author.display_avatar.url)
            await interaction.response.edit_message(embed=embed, view=None)

        except discord.Forbidden:
            await interaction.response.send_message("<a:olympus_WarnFlash:1380915318658174976> I don't have permission to ban this user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"<a:olympus_WarnFlash:1380915318658174976> Error: {e}", ephemeral=True)

        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="<:icon_cross:1381448030481547315>")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Ban cancelled.", embed=None, view=None)
        self.stop()

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ban",
        help="Bans a member with confirmation and hierarchy checks.",
        usage="ban <member> [reason]",
        aliases=["banmember"]
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_command(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        # Author checks
        if member == ctx.author:
            await ctx.send("<a:olympus_WarnFlash:1380915318658174976> You cannot ban yourself.")
            return

        if member == ctx.guild.owner:
            await ctx.send("<a:olympus_WarnFlash:1380915318658174976> You cannot ban the server owner.")
            return

        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("<a:olympus_WarnFlash:1380915318658174976> You cannot ban someone with an equal or higher role.")
            return

        # Bot role hierarchy check
        if member.top_role >= ctx.me.top_role:
            await ctx.send("<a:olympus_WarnFlash:1380915318658174976> I cannot ban this user due to role hierarchy.")
            return

        # Show confirmation view
        embed = discord.Embed(
            title="<a:olympus_WarnFlash:1380915318658174976> Do you really want to ban this member?",
            description=(
                f"👤 Member: {member.mention}\n"
                f"📄 Reason: {reason}\n\n"
                "Please confirm or cancel this action below."
            ),
            color=0xFFF700
        )
        view = ConfirmBanView(ctx, member, reason)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Ban(bot))