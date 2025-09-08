import discord
from discord.ext import commands
from utils.Tools import *
import json

class Vanityroles(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        with open('vanityroles.json', 'r') as f:
            self.config = json.load(f)

    def save_config(self):
        with open('vanityroles.json', 'w') as f:
            json.dump(self.config, f, indent=4)

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if after.guild is None:
            return

        guild_id = str(after.guild.id)

        if guild_id in self.config:
            vanity_status = self.config[guild_id].get("vanity")
            role_id = self.config[guild_id].get("role")
            channel_id = self.config[guild_id].get("channel")

            role = after.guild.get_role(role_id)
            channel = after.guild.get_channel(channel_id)

            before_activity_status = before.activity.name if before.activity else ""
            after_activity_status = after.activity.name if after.activity else ""

            if after_activity_status == vanity_status:
                if role and channel:
                    if role not in after.roles:
                        await after.add_roles(role)
                        embed = discord.Embed(
                            title="Vanity Added",
                            description=f"{after.mention} has been assigned the **{role.name}** role for repping vanity `{vanity_status}`!",
                            color=0x2f3136
                        )
                        embed.set_thumbnail(url=after.avatar.url)
                        await channel.send(embed=embed)

            elif before_activity_status == vanity_status and after_activity_status != vanity_status:
                if role in after.roles:
                    await after.remove_roles(role)
                    embed = discord.Embed(
                        title="Vanity Removed",
                        description=f"{after.mention} has been removed from the **{role.name}** role for no longer repping vanity `{vanity_status}`.",
                        color=0x2f3136
                    )
                    embed.set_thumbnail(url=after.avatar.url)
                    await channel.send(embed=embed)
    
    @commands.hybrid_group(name="vanityroles",
                           description="Setupsvanity roles for the server.",
                           help="Setups vanity roles for the server.",
                           aliases=['vr'])
    @blacklist_check()
    @commands.has_permissions(administrator=True)
    async def __vr(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @__vr.command(name="setup",
                  description="Setups vanity role for the server.",
                  help="Setups vanity role for the server.")
    @blacklist_check()
    @commands.has_permissions(administrator=True)
    async def _setup(self, ctx, vanity, role: discord.Role,
                     channel: discord.TextChannel):
        if ctx.author == ctx.guild.owner or ctx.guild.me.top_role <= ctx.author.top_role:
            if role.permissions.administrator or role.permissions.ban_members or role.permissions.kick_members:
                embed1 = discord.Embed(
                    description="Please select a role that doesn't have any dangerous permissions.",
                    color=0x2f3136)
                await ctx.send(embed=embed1)
            else:
                pop = {
                    "vanity": vanity,
                    "role": role.id,
                    "channel": channel.id
                }
                self.config[str(ctx.guild.id)] = pop
                embed = discord.Embed(color=0x2f3136)
                embed.set_author(
                    name=f"Vanity Roles Config For {ctx.guild.name}",
                    icon_url=f"{ctx.author.avatar}")
                embed.add_field(
                    name="Vanity",
                    value=f"{vanity}",
                    inline=False)
                embed.add_field(
                    name="Role",
                    value=f"{role.mention}",
                    inline=False)
                embed.add_field(
                    name="Channel",
                    value=f"{channel.mention}",
                    inline=False)
                await ctx.send(embed=embed)
                self.save_config()
        else:
            hacker5 = discord.Embed(
                description="""```diff\n - You must have Administrator permission.\n - Your top role should be above my top role. \n```""",
                color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")
            await ctx.reply(embed=hacker5, mention_author=False)

    @__vr.command(name="reset",
                  description="Reset vanity role for the server.",
                  help="Reset vanity role for the server.")
    @blacklist_check()
    @commands.has_permissions(administrator=True)
    async def ___reset(self, ctx):
        if ctx.author == ctx.guild.owner or ctx.guild.me.top_role <= ctx.author.top_role:
            if str(ctx.guild.id) not in self.config:
                embed1 = discord.Embed(
                    description="<:icon_cross:1381448030481547315> This server doesn't have any vanity roles set up yet.",
                    color=0x2f3136)
                await ctx.reply(embed=embed1, mention_author=False)
            else:
                self.config.pop(str(ctx.guild.id))
                await ctx.reply("Vanity Role System Removed For This Guild.", mention_author=False)
                self.save_config()
        else:
            hacker5 = discord.Embed(
                description="""```diff\n - You must have Administrator permission.\n - Your top role should be above my top role. \n```""",
                color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")
            await ctx.reply(embed=hacker5, mention_author=False)

    @__vr.command(name="show",
                  aliases=['config'],
                  description="Shows vanity role config for the server.",
                  help="Shows vanity role config for the server.")
    @blacklist_check()
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        if str(ctx.guild.id) not in self.config:
            embed1 = discord.Embed(
                description="<:icon_cross:1381448030481547315> This server doesn't have any vanity roles set up yet.",
                color=0x2f3136)
            await ctx.reply(embed=embed1, mention_author=False)
        else:
            vanity = self.config[str(ctx.guild.id)]["vanity"]
            role = self.config[str(ctx.guild.id)]["role"]
            channel = self.config[str(ctx.guild.id)]["channel"]
            lundchannel = self.bot.get_channel(channel)
            randirole = ctx.guild.get_role(role)
            embed = discord.Embed(color=0x2f3136)

            embed.add_field(name="Vanity",
                            value=f"{vanity}",
                            inline=False)
            embed.add_field(name="Role",
                            value=f"{randirole.mention}",
                            inline=False)
            embed.add_field(name="Channel",
                            value=f"{lundchannel.mention}",
                            inline=False)
            embed.set_author(name=f"Vanity Role Config For {ctx.guild.name}",
                             icon_url=f"{ctx.author.avatar}")
            await ctx.send(embed=embed, mention_author=False)

# Add the setup function to add the cog to the bot
def setup(bot):
    bot.add_cog(Vanityroleslol(bot))