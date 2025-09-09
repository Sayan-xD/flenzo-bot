import discord
from discord.ext import commands

class SayanOp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild

        print(f"[DMOnJoin] {member} joined {guild.name}")

        # Buttons view
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="➕ Add Me", url="https://discord.com/oauth2/authorize?client_id=998547879201349693&permissions=8&integration_type=0&scope=bot"))
        view.add_item(discord.ui.Button(label="🆘 Support Server", url="https://discord.gg/C86nD33WBr"))

        # Embed message
        embed = discord.Embed(
            title=f"Welcome to {guild.name}!",
            description=(
                f"Thanks for joining **{guild.name}**!\n"
                "I'm **Flenzo**, the best multipurpose bot here.\n\n"
                "You can add me to your own server or get help using the buttons below!"
            ),
            color=discord.Color.yellow()
        )

        try:
            await member.send(content="[Flenzo](https://discord.gg/C86nD33WBr)", embed=embed, view=view)
            print(f"[DMOnJoin] Successfully sent DM to {member}")
        except discord.Forbidden:
            print(f"[DMOnJoin] ❌ Could not DM {member} — DMs are off or blocked.")

# Async setup
async def setup(bot):
    await bot.add_cog(SayanOp(bot))
