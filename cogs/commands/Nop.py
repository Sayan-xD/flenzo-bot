import discord
from discord.ext import commands, tasks
import aiosqlite
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import logging
from typing import Optional

# ----- Config -----
ROLE_ID = 1395964329915846656
GUILD_ID = 968855422423404606
LOG_CHANNEL_ID = 1397581994791272479
NP_DB_PATH = "db/np.db"
EMOJI_TICK = "<:IconTick:1381245157759782975>"
EMOJI_CROSS = "<:icon_cross:1381448030481547315>"

# Setup basic logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("NoPrefix")

# -------------------- VIEW --------------------
class ClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # persistent view

    @discord.ui.button(
        label="Claim Now",
        style=discord.ButtonStyle.success,
        emoji="🔓",
        custom_id="np_claim_button"
    )
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button callback for claiming No Prefix access."""
        await interaction.response.defer(ephemeral=True)  # allow time for DB / role ops

        user = interaction.user
        user_id = user.id
        claimed_at = datetime.utcnow()
        expires_at = claimed_at + timedelta(days=7)

        # DB insert / check
        try:
            async with aiosqlite.connect(NP_DB_PATH) as db:
                # ensure tables exist (harmless if already created in setup)
                await db.execute(
                    "CREATE TABLE IF NOT EXISTS np (id INTEGER PRIMARY KEY, expiry_time TEXT NOT NULL, claimed_at TEXT NOT NULL)"
                )
                await db.execute(
                    "CREATE TABLE IF NOT EXISTS np_claimed (id INTEGER PRIMARY KEY, claimed_at TEXT NOT NULL)"
                )
                await db.commit()

                # Check one-time claim
                async with db.execute("SELECT 1 FROM np_claimed WHERE id = ?", (user_id,)) as cur:
                    if await cur.fetchone():
                        await interaction.followup.send(
                            f"{EMOJI_CROSS} You have already claimed No Prefix access. This is a one-time offer.",
                            ephemeral=True
                        )
                        return

                # Insert into np and np_claimed
                await db.execute(
                    "INSERT INTO np (id, expiry_time, claimed_at) VALUES (?, ?, ?)",
                    (user_id, expires_at.isoformat(), claimed_at.isoformat())
                )
                await db.execute("INSERT INTO np_claimed (id, claimed_at) VALUES (?, ?)", (user_id, claimed_at.isoformat()))
                await db.commit()
        except Exception as e:
            log.exception(f"DB error while user {user_id} tried to claim: {e}")
            await interaction.followup.send(f"{EMOJI_CROSS} Something went wrong while processing your claim. Try again later.", ephemeral=True)
            return

        # Give role (with fetch fallback)
        try:
            guild: Optional[discord.Guild] = interaction.client.get_guild(GUILD_ID)
            member: Optional[discord.Member] = None
            if guild:
                member = guild.get_member(user_id)
                if member is None:
                    try:
                        member = await guild.fetch_member(user_id)
                    except Exception:
                        member = None

            if guild and member:
                role = guild.get_role(ROLE_ID)
                if role:
                    try:
                        await member.add_roles(role, reason="Claimed No Prefix Trial")
                    except discord.Forbidden:
                        log.warning(f"Missing permission to add role to {user_id}.")
                    except Exception as e:
                        log.exception(f"Failed to add role to {user_id}: {e}")
        except Exception as e:
            log.exception(f"Unexpected error during role add for {user_id}: {e}")

        # DM user (best-effort)
        try:
            dm_embed = discord.Embed(
                title=f"{EMOJI_TICK} No Prefix Access Granted!",
                description="You’ve claimed **No Prefix Access** for **7 days**.\nEnjoy using commands without prefix!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            await user.send(embed=dm_embed)
        except Exception:
            # often users disable DMs from server members - that's okay
            log.info(f"Could not DM user {user_id} (might have DMs closed).")

        # Confirm to the user (ephemeral)
        await interaction.followup.send(
            f"{EMOJI_TICK} You have successfully claimed 7-day No Prefix Access!",
            ephemeral=True
        )

        # Log to configured channel (best-effort)
        try:
            log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
            if log_channel is None:
                try:
                    log_channel = await interaction.client.fetch_channel(LOG_CHANNEL_ID)
                except Exception:
                    log_channel = None

            if log_channel:
                embed = discord.Embed(
                    title=f"{EMOJI_TICK} No Prefix Claimed",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="User", value=f"{user.mention} (`{user_id}`)", inline=False)
                embed.add_field(name="Claimed At", value=f"<t:{int(claimed_at.timestamp())}:F>")
                embed.add_field(name="Expires At", value=f"<t:{int(expires_at.timestamp())}:F>")
                await log_channel.send(embed=embed)
        except Exception:
            log.exception(f"Failed to send log message for claim by {user_id}.")


# -------------------- COG --------------------
class NoPrefixClaim(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # start the expiry checker loop (before_loop will wait until ready)
        self.expiry_check.start()

    def cog_unload(self):
        # ensure the background task is cancelled on cog unload/reload
        try:
            self.expiry_check.cancel()
        except Exception:
            pass

    @commands.is_owner()
    @commands.command(name="npclaim")
    async def npclaim(self, ctx: commands.Context):
        """Send the No Prefix claim embed (Owner only)"""
        embed = discord.Embed(
            title="🔓 Claim 7-Day No Prefix Trial",
            description="Click below to get **No Prefix Access** for 7 days.\n> ⚠️ You can only claim this once.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Access is automatically removed after 7 days.")
        await ctx.send(embed=embed, view=ClaimView())

    @commands.is_owner()
    @commands.command(name="freenplist")
    async def freenp_list(self, ctx: commands.Context):
        """List users who have claimed free No Prefix access"""
        async with aiosqlite.connect(NP_DB_PATH) as db:
            async with db.execute("SELECT id, expiry_time FROM np ORDER BY expiry_time ASC") as cursor:
                rows = await cursor.fetchall()

        if not rows:
            return await ctx.send(f"{EMOJI_CROSS} No one has claimed No Prefix access yet.")

        entries = []
        for uid, expiry in rows:
            try:
                expires_at = datetime.fromisoformat(expiry)
                entries.append(f"<@{uid}> - Expires <t:{int(expires_at.timestamp())}:R>")
            except Exception:
                entries.append(f"<@{uid}> - Expires (invalid date stored)")

        pages = [entries[i:i+10] for i in range(0, len(entries), 10)]
        for i, page in enumerate(pages, start=1):
            embed = discord.Embed(
                title=f"🔓 No Prefix Claimed Users ({len(rows)}) - Page {i}/{len(pages)}",
                description="\n".join(page),
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(name="purgefreenp")
    async def purge_freenp(self, ctx: commands.Context):
        """Purge all saved No Prefix claim data (owner only)"""
        async with aiosqlite.connect(NP_DB_PATH) as db:
            await db.execute("DELETE FROM np")
            await db.execute("DELETE FROM np_claimed")
            await db.commit()

        embed = discord.Embed(
            title=f"{EMOJI_TICK} No Prefix Data Purged",
            description="All saved No Prefix claims have been deleted.\nEveryone can now claim again.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        await ctx.send(embed=embed)

        try:
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel is None:
                try:
                    log_channel = await self.bot.fetch_channel(LOG_CHANNEL_ID)
                except Exception:
                    log_channel = None

            if log_channel:
                log_embed = discord.Embed(
                    title=f"{EMOJI_CROSS} No Prefix Database Reset",
                    description=f"All claim records have been wiped by {ctx.author.mention}.",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                await log_channel.send(embed=log_embed)
        except Exception:
            log.exception("Failed to send purge log message.")

    @tasks.loop(minutes=5)
    async def expiry_check(self):
        """Auto remove role when 7-day access expires"""
        now = datetime.utcnow()

        try:
            async with aiosqlite.connect(NP_DB_PATH) as db:
                async with db.execute("SELECT id, expiry_time FROM np") as cursor:
                    rows = await cursor.fetchall()

                for user_id, expiry_str in rows:
                    try:
                        expiry = datetime.fromisoformat(expiry_str)
                    except Exception:
                        log.warning(f"Invalid expiry stored for {user_id}: {expiry_str}. Removing row.")
                        await db.execute("DELETE FROM np WHERE id = ?", (user_id,))
                        await db.commit()
                        continue

                    if expiry <= now:
                        guild = self.bot.get_guild(GUILD_ID)
                        member = None
                        if guild:
                            member = guild.get_member(user_id)
                            if member is None:
                                try:
                                    member = await guild.fetch_member(user_id)
                                except Exception:
                                    member = None

                        role = guild.get_role(ROLE_ID) if guild else None

                        # try to remove role if present
                        if member and role and role in member.roles:
                            try:
                                await member.remove_roles(role, reason="No Prefix expired")
                            except discord.Forbidden:
                                log.warning(f"Missing permissions to remove role from {user_id}.")
                            except Exception:
                                log.exception(f"Failed to remove role from {user_id} on expiry.")

                        # always remove DB row even if role removal failed
                        await db.execute("DELETE FROM np WHERE id = ?", (user_id,))
                        await db.commit()

                        # send log message (best-effort)
                        try:
                            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
                            if log_channel is None:
                                try:
                                    log_channel = await self.bot.fetch_channel(LOG_CHANNEL_ID)
                                except Exception:
                                    log_channel = None

                            if log_channel:
                                embed = discord.Embed(
                                    title=f"{EMOJI_CROSS} No Prefix Access Expired",
                                    color=discord.Color.red(),
                                    timestamp=datetime.utcnow()
                                )
                                embed.add_field(name="User", value=f"<@{user_id}> (`{user_id}`)")
                                await log_channel.send(embed=embed)
                        except Exception:
                            log.exception(f"Failed to send expiry log for {user_id}.")
        except Exception:
            log.exception("Error while running expiry_check loop.")

    @expiry_check.before_loop
    async def before_expiry(self):
        await self.bot.wait_until_ready()


# -------------------- SETUP --------------------
async def setup(bot: commands.Bot):
    # ensure DB directory exists
    db_path = Path(NP_DB_PATH)
    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    # create necessary tables once at setup
    try:
        async with aiosqlite.connect(NP_DB_PATH) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS np (id INTEGER PRIMARY KEY, expiry_time TEXT NOT NULL, claimed_at TEXT NOT NULL)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS np_claimed (id INTEGER PRIMARY KEY, claimed_at TEXT NOT NULL)"
            )
            await db.commit()
    except Exception:
        log.exception("Failed to initialize NP database tables during setup.")

    # register persistent view and add cog
    bot.add_view(ClaimView())
    await bot.add_cog(NoPrefixClaim(bot))
    log.info("NoPrefixClaim cog loaded and ClaimView registered.")
