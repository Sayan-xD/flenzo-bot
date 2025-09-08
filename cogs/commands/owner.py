from discord.ext import commands
import discord
import json
import asyncio
import aiosqlite
from utils import Paginator, DescriptionEmbedPaginator
from utils.Tools import *
from utils.config import OWNER_IDS
from core import Context


def load_owner_ids():
    return OWNER_IDS

async def is_staff(user, staff_ids):
    return user.id in staff_ids

async def is_owner_or_staff(ctx):
    return await is_staff(ctx.author, ctx.cog.staff) or ctx.author.id in OWNER_IDS


class Owner(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.staff = set()
        self.np_cache = []
        self.db_path = 'db/np.db'
        self.stop_tour = False
        self.bot_owner_ids = OWNER_IDS
        self.client.loop.create_task(self.setup_database())
        self.client.loop.create_task(self.load_staff())

    async def setup_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY)')
            await db.commit()

    async def load_staff(self):
        await self.client.wait_until_ready()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT id FROM staff') as cursor:
                self.staff = {row[0] for row in await cursor.fetchall()}

    @commands.command(name="staff_add")
    @commands.is_owner()
    async def staff_add(self, ctx, user: discord.User):
        if user.id in self.staff:
            await ctx.reply(embed=discord.Embed(title="Already Exists", description=f"{user} is already in staff list.", color=0x000000))
        else:
            self.staff.add(user.id)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('INSERT OR IGNORE INTO staff (id) VALUES (?)', (user.id,))
                await db.commit()
            await ctx.reply(embed=discord.Embed(title="Success", description=f"{user} added to staff list.", color=0x000000))

    @commands.command(name="staff_remove")
    @commands.is_owner()
    async def staff_remove(self, ctx, user: discord.User):
        if user.id not in self.staff:
            await ctx.reply(embed=discord.Embed(title="Not Found", description=f"{user} is not in staff list.", color=0x000000))
        else:
            self.staff.remove(user.id)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM staff WHERE id = ?', (user.id,))
                await db.commit()
            await ctx.reply(embed=discord.Embed(title="Success", description=f"{user} removed from staff list.", color=0x000000))

    @commands.command(name="staff_list")
    @commands.is_owner()
    async def staff_list(self, ctx):
        if not self.staff:
            await ctx.send("The staff list is empty.")
            return
        entries = [f"{(await self.client.fetch_user(uid)).mention} (ID: {uid})" for uid in self.staff]
        paginator = Paginator(source=DescriptionEmbedPaginator(entries=entries, title="Flenzo Staff Members", per_page=10, color=0x000000), ctx=ctx)
        await paginator.paginate()

    @commands.command(name="slist")
    @commands.check(is_owner_or_staff)
    async def _slist(self, ctx):
        servers = sorted(self.client.guilds, key=lambda g: g.member_count, reverse=True)
        entries = [f"`#{i}` | [{g.name}](https://discord.com/guilds/{g.id}) - {g.member_count}" for i, g in enumerate(servers, 1)]
        paginator = Paginator(source=DescriptionEmbedPaginator(entries=entries, title=f"Guilds [{len(servers)}]", per_page=10, color=0x000000), ctx=ctx)
        await paginator.paginate()

    @commands.command(name="mutuals")
    @commands.is_owner()
    async def mutuals(self, ctx, user: discord.User):
        guilds = [g for g in self.client.guilds if user in g.members]
        entries = [f"`#{i}` | [{g.name}](https://discord.com/channels/{g.id}) - {g.member_count}" for i, g in enumerate(guilds, 1)]
        paginator = Paginator(source=DescriptionEmbedPaginator(entries=entries, title=f"Mutual Guilds with {user}", per_page=10, color=0x000000), ctx=ctx)
        await paginator.paginate()

    @commands.command(name="restart")
    @commands.is_owner()
    async def _restart(self, ctx: Context):
        await ctx.reply("Restarting...")
        restart_program()

    @commands.command(name="owners")
    @commands.is_owner()
    async def own_list(self, ctx):
        entries = [f"`#{i}` | [{(await self.client.fetch_user(uid)).mention}](https://discord.com/users/{uid})" for i, uid in enumerate(OWNER_IDS, 1)]
        paginator = Paginator(source=DescriptionEmbedPaginator(entries=entries, title="Flenzo Bot Owners", per_page=10, color=0x000000), ctx=ctx)
        await paginator.paginate()

    @commands.command(name="leaveguild")
    @commands.is_owner()
    async def leave_guild(self, ctx, guild_id: int):
        guild = self.client.get_guild(guild_id)
        if guild:
            await guild.leave()
            await ctx.send(f"Left the guild: {guild.name} ({guild.id})")
        else:
            await ctx.send("Guild not found.")

    @commands.command(name="dm")
    @commands.is_owner()
    async def dm(self, ctx, user: discord.User, *, message: str):
        try:
            await user.send(message)
            await ctx.send(f"Message sent to {user}.")
        except discord.Forbidden:
            await ctx.send("Couldn't DM the user. They may have DMs closed or are a bot.")

# Don't forget to add setup
async def setup(bot):
    await bot.add_cog(Owner(bot))