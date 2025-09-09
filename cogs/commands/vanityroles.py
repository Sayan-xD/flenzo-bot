import discord
from discord.ext import commands
from utils.Tools import *
import aiosqlite


class Vanityroles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        """Ensure database and table exist when cog loads."""
        async with aiosqlite.connect("db/vanityroles.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS vanityroles (
                    guild_id INTEGER PRIMARY KEY,
                    vanity TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL
                )
            """)
            await db.commit()

    async def get_config(self, guild_id: int):
        async with aiosqlite.connect("db/vanityroles.db") as db:
            cursor = await db.execute("SELECT vanity, role_id, channel_id FROM vanityroles WHERE guild_id = ?", (guild_id,))
            row = await cursor.fetchone()
            return row  # None if not set

    async def set_config(self, guild_id: int, vanity: str, role_id: int, channel_id: int):
        async with aiosqlite.connect("db/vanityroles.db") as db:
            await db.execute("""
                INSERT INTO vanityroles (guild_id, vanity, role_id, channel_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    vanity = excluded.vanity,
                    role_id = excluded.role_id,
                    channel_id = excluded.channel_id
            """, (guild_id, vanity, role_id, channel_id))
            await db.commit()

    async def reset_config(self, guild_id: int):
        async with aiosqlite.connect("db/vanityroles.db") as db:
            await db.execute("DELETE FROM vanityroles WHERE guild_id = ?", (guild_id,))
            await db.commit()

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if after.guild is None:
            return

        config = await self.get_config(after.guild.id)
        if not config:
            return

        vanity_status, role_id, channel_id = config
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
                    embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
                    await channel.send(embed=embed)

        elif before_activity_status == vanity_status and after_activity_status != vanity_status:
            if role in after.roles:
                await after.remove_roles(role)
                if channel:
                    embed = discord.Embed(
                        title="Vanity Removed",
                        description=f"{after.mention} has been removed from the **{role.name}** role for no longer repping vanity `{vanity_status}`.",
                        color=0x2f3136
                    )
                    embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
                    await channel.send(embed=embed)

    @commands.hybrid_group(
        name="vanityroles",
        description="Setup vanity roles for the server.",
        help="Setup vanity roles for the server.",
        aliases=['vr']
    )
    @blacklist_check()
    @commands.has_permissions(administrator=True)
    async def __vr(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @__vr.command(name="setup", description="Setup vanity role for the server.")
    @blacklist_check()
    @commands.has_permissions(administrator=True)
    async def _setup(self, ctx, vanity: str, role: discord.Role, channel: discord.TextChannel):
        if ctx.author == ctx.guild.owner or ctx.author.top_role > ctx.guild.me.top_role:
            if role.permissions.administrator or role.permissions.ban_members or role.permissions.kick_members:
                embed1 = discord.Embed(
                    description="<:icon_cross:1381448030481547315> Please select a role that doesn't have dangerous permissions.",
                    color=0x2f3136
                )
                await ctx.send(embed=embed1)
            else:
                await self.set_config(ctx.guild.id, vanity, role.id, channel.id)
                embed = discord.Embed(color=0x2f3136)
                embed.set_author(
                    name=f"Vanity Roles Config For {ctx.guild.name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
                )
                embed.add_field(name="Vanity", value=f"{vanity}", inline=False)
                embed.add_field(name="Role", value=f"{role.mention}", inline=False)
                embed.add_field(name="Channel", value=f"{channel.mention}", inline=False)
                await ctx.send(embed=embed)
        else:
            hacker5 = discord.Embed(
                description="""```diff
- You must have Administrator permission.
- Your top role should be above my top role. 
```""",
                color=0x2f3136
            )
            hacker5.set_author(
                name=f"{ctx.author.name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            )
            await ctx.reply(embed=hacker5, mention_author=False)

    @__vr.command(name="reset", description="Reset vanity role for the server.")
    @blacklist_check()
    @commands.has_permissions(administrator=True)
    async def ___reset(self, ctx):
        if ctx.author == ctx.guild.owner or ctx.author.top_role > ctx.guild.me.top_role:
            config = await self.get_config(ctx.guild.id)
            if not config:
                embed1 = discord.Embed(
                    description="<:icon_cross:1381448030481547315> This server doesn't have any vanity roles set up yet.",
                    color=0x2f3136
                )
                await ctx.reply(embed=embed1, mention_author=False)
            else:
                await self.reset_config(ctx.guild.id)
                embed = discord.Embed(
                    description="<:IconTick:1381245157759782975> Vanity Role System Removed For This Guild.",
                    color=0x2f3136
                )
                await ctx.reply(embed=embed, mention_author=False)
        else:
            hacker5 = discord.Embed(
                description="""```diff
- You must have Administrator permission.
- Your top role should be above my top role. 
```""",
                color=0x2f3136
            )
            hacker5.set_author(
                name=f"{ctx.author.name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            )
            await ctx.reply(embed=hacker5, mention_author=False)

    @__vr.command(name="show", aliases=['config'], description="Show vanity role config.")
    @blacklist_check()
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        config = await self.get_config(ctx.guild.id)
        if not config:
            embed1 = discord.Embed(
                description="<:icon_cross:1381448030481547315> This server doesn't have any vanity roles set up yet.",
                color=0x2f3136
            )
            await ctx.reply(embed=embed1, mention_author=False)
        else:
            vanity, role_id, channel_id = config
            role = ctx.guild.get_role(role_id)
            channel = self.bot.get_channel(channel_id)

            embed = discord.Embed(color=0x2f3136)
            embed.add_field(name="Vanity", value=f"{vanity}", inline=False)
            embed.add_field(name="Role", value=f"{role.mention if role else 'Deleted Role'}", inline=False)
            embed.add_field(name="Channel", value=f"{channel.mention if channel else 'Deleted Channel'}", inline=False)
            embed.set_author(
                name=f"Vanity Role Config For {ctx.guild.name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            )
            await ctx.send(embed=embed, mention_author=False)


def setup(bot):
    bot.add_cog(Vanityroles(bot))
