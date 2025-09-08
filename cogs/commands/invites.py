import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os

class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invite_cache = {}

        os.makedirs("db", exist_ok=True)
        with sqlite3.connect("db/invites.db") as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS invites (
                    user_id INTEGER,
                    inviter_id INTEGER,
                    guild_id INTEGER,
                    join_time TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    inviter_id INTEGER,
                    guild_id INTEGER,
                    total INTEGER DEFAULT 0,
                    real INTEGER DEFAULT 0,
                    fake INTEGER DEFAULT 0,
                    left INTEGER DEFAULT 0,
                    rejoins INTEGER DEFAULT 0,
                    PRIMARY KEY (inviter_id, guild_id)
                )
            """)
            conn.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if guild.me.guild_permissions.manage_guild:
                try:
                    invites = await guild.invites()
                    self.invite_cache[guild.id] = {invite.code: invite.uses for invite in invites}
                except Exception as e:
                    print(f"[on_ready] Error fetching invites for {guild.name}: {e}")
            else:
                print(f"[on_ready] Missing Manage Server permission in {guild.name}")
        try:
            await self.bot.tree.sync()
            print("✅ Slash commands synced.")
        except Exception as e:
            print(f"❌ Failed to sync slash commands: {e}")
        print("✅ Invite cache initialized")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.guild.me.guild_permissions.manage_guild:
            print(f"[on_member_join] Missing Manage Server permission in {member.guild.name}")
            return

        before = self.invite_cache.get(member.guild.id, {})
        try:
            invites = await member.guild.invites()
        except Exception as e:
            print(f"[on_member_join] Failed to fetch invites: {e}")
            return

        used = None
        for invite in invites:
            if invite.code in before and invite.uses > before[invite.code]:
                used = invite
                break

        self.invite_cache[member.guild.id] = {i.code: i.uses for i in invites}

        if used:
            inviter = used.inviter
            with sqlite3.connect("db/invites.db") as conn:
                c = conn.cursor()
                c.execute("SELECT inviter_id FROM invites WHERE user_id = ? AND guild_id = ?", (member.id, member.guild.id))
                previous = c.fetchone()

                if previous:
                    c.execute("""
                        INSERT INTO stats (inviter_id, guild_id, rejoins)
                        VALUES (?, ?, ?)
                        ON CONFLICT(inviter_id, guild_id) DO UPDATE SET
                        rejoins = rejoins + 1
                    """, (inviter.id, member.guild.id, 1))
                else:
                    c.execute("INSERT INTO invites (user_id, inviter_id, guild_id, join_time) VALUES (?, ?, ?, ?)",
                              (member.id, inviter.id, member.guild.id, discord.utils.utcnow().isoformat()))

                    is_fake = (discord.utils.utcnow() - member.created_at).days < 90
                    if not is_fake:
                        c.execute("""
                            INSERT INTO stats (inviter_id, guild_id, total, real)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(inviter_id, guild_id) DO UPDATE SET
                            total = total + 1, real = real + 1
                        """, (inviter.id, member.guild.id, 1, 1))
                    else:
                        c.execute("""
                            INSERT INTO stats (inviter_id, guild_id, fake)
                            VALUES (?, ?, ?)
                            ON CONFLICT(inviter_id, guild_id) DO UPDATE SET
                            fake = fake + 1
                        """, (inviter.id, member.guild.id, 1))
                conn.commit()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        with sqlite3.connect("db/invites.db") as conn:
            c = conn.cursor()
            c.execute("SELECT inviter_id, join_time FROM invites WHERE user_id = ? AND guild_id = ?", (member.id, member.guild.id))
            row = c.fetchone()
            if row:
                inviter_id, join_time = row
                try:
                    join_dt = discord.utils.parse_time(join_time)
                except Exception:
                    join_dt = discord.utils.utcnow()

                is_fake = (join_dt - member.created_at).days < 90

                if not is_fake:
                    c.execute("""
                        UPDATE stats SET 
                            real = CASE WHEN real > 0 THEN real - 1 ELSE 0 END,
                            total = CASE WHEN total > 0 THEN total - 1 ELSE 0 END,
                            left = left + 1
                        WHERE inviter_id = ? AND guild_id = ?
                    """, (inviter_id, member.guild.id))
                else:
                    c.execute("""
                        UPDATE stats SET 
                            fake = CASE WHEN fake > 0 THEN fake - 1 ELSE 0 END,
                            left = left + 1
                        WHERE inviter_id = ? AND guild_id = ?
                    """, (inviter_id, member.guild.id))
                conn.commit()

    @commands.command(name="invites", aliases=["i"])
    async def invites_prefix(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        with sqlite3.connect("db/invites.db") as conn:
            c = conn.cursor()
            c.execute("""
                SELECT total, real, fake, left, rejoins FROM stats
                WHERE inviter_id = ? AND guild_id = ?
            """, (member.id, ctx.guild.id))
            row = c.fetchone()

        total, real, fake, left, rejoins = row if row else (0, 0, 0, 0, 0)

        embed = discord.Embed(
            title="Invite log",
            description=f"**<:Vanity_Roles:1383631102887067688> {member.display_name} has {total} invites**",
            color=discord.Color.yellow()
        )
        embed.add_field(name="​", value=(
            f"<:rp_arrow:1383632907267997716> **Joins : {total}\n**"
            f"<:rp_arrow:1383632907267997716> **Left : {left}\n**"
            f"<:rp_arrow:1383632907267997716> **Fake : {fake}\n**"
            f"<:rp_arrow:1383632907267997716> **Rejoins : {rejoins}\n\n**<:icons_plus:1381456773554114623> **Enjoy Lifetime Invites Tracking With** [Flenzo](https://discord.com/oauth2/authorize?client_id=998547879201349693)"
            
        ), inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="inviter")
    async def inviter_prefix(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        with sqlite3.connect("db/invites.db") as conn:
            c = conn.cursor()
            c.execute("SELECT inviter_id FROM invites WHERE user_id = ? AND guild_id = ?", (member.id, ctx.guild.id))
            row = c.fetchone()

        if row:
            inviter_id = row[0]
            inviter_member = ctx.guild.get_member(inviter_id)
            inviter_name = inviter_member.display_name if inviter_member else "Unknown User"
            await ctx.send(f"🔍 **{member.display_name}** was invited by **{inviter_name}**.")
        else:
            await ctx.send(f"❌ No inviter record found for **{member.display_name}**.")

    @commands.command(name="resetinvites", aliases=["reset invites"])
    @commands.has_permissions(administrator=True)
    async def reset_invites(self, ctx, member: discord.Member):
        with sqlite3.connect("db/invites.db") as conn:
            c = conn.cursor()
            c.execute("DELETE FROM stats WHERE inviter_id = ? AND guild_id = ?", (member.id, ctx.guild.id))
            c.execute("DELETE FROM invites WHERE inviter_id = ? AND guild_id = ?", (member.id, ctx.guild.id))
            conn.commit()
        await ctx.send(f"<:IconTick:1381245157759782975> Succesfully Reset {member.display_name}'s Invites")

    @commands.command(name="resetinvitesall")
    @commands.has_permissions(administrator=True)
    async def reset_invites_all(self, ctx):
        with sqlite3.connect("db/invites.db") as conn:
            c = conn.cursor()
            c.execute("DELETE FROM stats WHERE guild_id = ?", (ctx.guild.id,))
            c.execute("DELETE FROM invites WHERE guild_id = ?", (ctx.guild.id,))
            conn.commit()
        await ctx.send("✅ All invite stats reset for this server.")

async def setup(bot):
    await bot.add_cog(InviteTracker(bot))
