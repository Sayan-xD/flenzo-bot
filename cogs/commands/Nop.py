import discord
from discord.ext import commands, tasks
import aiosqlite
from datetime import datetime, timedelta

# Config
ROLE_ID = 1395964329915846656
GUILD_ID = 968855422423404606
LOG_CHANNEL_ID = 1397581994791272479
NP_DB_PATH = "db/np.db"
EMOJI_TICK = "<:IconTick:1381245157759782975>"
EMOJI_CROSS = "<:icon_cross:1381448030481547315>"

# -------------------- VIEW --------------------
class ClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim Now", style=discord.ButtonStyle.success, emoji="🔓", custom_id="np_claim_button")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        user_id = user.id
        claimed_at = datetime.utcnow()
        expires_at = claimed_at + timedelta(days=7)

        async with aiosqlite.connect(NP_DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS np (
                    id INTEGER PRIMARY KEY,
                    expiry_time TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS np_claimed (
                    id INTEGER PRIMARY KEY
                )
            """)
            await db.commit()

            # Check if user already claimed
            async with db.execute("SELECT id FROM np_claimed WHERE id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return await interaction.response.send_message(
                        f"{EMOJI_CROSS} You have already claimed No Prefix access. This is a one-time offer.",
                        ephemeral=True
                    )

            # Insert into np and np_claimed
            await db.execute("INSERT INTO np (id, expiry_time) VALUES (?, ?)", (user_id, expires_at.isoformat()))
            await db.execute("INSERT INTO np_claimed (id) VALUES (?)", (user_id,))
            await db.commit()

        # Add role
        guild = interaction.client.get_guild(GUILD_ID)
        if guild:
            member = guild.get_member(user_id)
            if member:
                role = guild.get_role(ROLE_ID)
                if role:
                    await member.add_roles(role, reason="Claimed No Prefix Trial")

        # DM
        try:
            await user.send(embed=discord.Embed(
                title=f"{EMOJI_TICK} No Prefix Access Granted!",
                description="You’ve claimed **No Prefix Access** for **7 days**.\nEnjoy using commands without prefix!",
                color=discord.Color.green()
            ))
        except:
            pass

        await interaction.response.send_message(
            f"{EMOJI_TICK} You have successfully claimed 7-day No Prefix Access!",
            ephemeral=True
        )

        # Log
        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title=f"{EMOJI_TICK} No Prefix Claimed", color=discord.Color.green())
            embed.add_field(name="User", value=f"{user.mention} (`{user_id}`)", inline=False)
            embed.add_field(name="Claimed At", value=f"<t:{int(claimed_at.timestamp())}:F>")
            embed.add_field(name="Expires At", value=f"<t:{int(expires_at.timestamp())}:F>")
            embed.timestamp = datetime.utcnow()
            await log_channel.send(embed=embed)

# -------------------- COG --------------------
class NoPrefixClaim(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.expiry_check.start()

    @commands.is_owner()
    @commands.command(name="npclaim")
    async def npclaim(self, ctx):
        """Send the No Prefix claim embed (Owner only)"""
        embed = discord.Embed(
            title="🔓 Claim 7-Day No Prefix Trial",
            description="Click below to get **No Prefix Access** for 7 days.\n> ⚠️ You can only claim this once.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Access is automatically removed after 7 days.")
        await ctx.send(embed=embed, view=ClaimView())

    @tasks.loop(minutes=5)
    async def expiry_check(self):
        """Auto remove role when 7-day access expires"""
        now = datetime.utcnow().isoformat()

        async with aiosqlite.connect(NP_DB_PATH) as db:
            async with db.execute("SELECT id, expiry_time FROM np") as cursor:
                rows = await cursor.fetchall()

            for user_id, expiry_str in rows:
                if expiry_str <= now:
                    guild = self.bot.get_guild(GUILD_ID)
                    member = guild.get_member(user_id) if guild else None
                    role = guild.get_role(ROLE_ID) if guild else None

                    if member and role and role in member.roles:
                        await member.remove_roles(role, reason="No Prefix expired")

                    # Remove from DB
                    await db.execute("DELETE FROM np WHERE id = ?", (user_id,))
                    await db.commit()

                    # Log
                    log = self.bot.get_channel(LOG_CHANNEL_ID)
                    if log:
                        embed = discord.Embed(
                            title=f"{EMOJI_CROSS} No Prefix Access Expired",
                            color=discord.Color.red()
                        )
                        embed.add_field(name="User", value=f"<@{user_id}> (`{user_id}`)")
                        embed.timestamp = datetime.utcnow()
                        await log.send(embed=embed)

    @expiry_check.before_loop
    async def before_expiry(self):
        await self.bot.wait_until_ready()

    @commands.is_owner()
    @commands.command(name="freenplist")
    async def freenp_list(self, ctx):
        """List users who have claimed free No Prefix access"""
        async with aiosqlite.connect(NP_DB_PATH) as db:
            async with db.execute("SELECT id, expiry_time FROM np") as cursor:
                rows = await cursor.fetchall()

        if not rows:
            return await ctx.send(f"{EMOJI_CROSS} No one has claimed No Prefix access yet.")

        entries = []
        for uid, expiry in rows:
            expires_at = datetime.fromisoformat(expiry)
            entries.append(f"<@{uid}> - Expires <t:{int(expires_at.timestamp())}:R>")

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
    async def purge_freenp(self, ctx):
        """Purge all saved No Prefix claim data (owner only)"""
        async with aiosqlite.connect(NP_DB_PATH) as db:
            await db.execute("DELETE FROM np")
            await db.execute("DELETE FROM np_claimed")
            await db.commit()

        embed = discord.Embed(
            title=f"{EMOJI_TICK} No Prefix Data Purged",
            description="All saved No Prefix claims have been deleted.\nEveryone can now claim again.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title=f"{EMOJI_CROSS} No Prefix Database Reset",
                description=f"All claim records have been wiped by {ctx.author.mention}.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            await log_channel.send(embed=log_embed)

# -------------------- SETUP --------------------
async def setup(bot):
    bot.add_view(ClaimView())
    await bot.add_cog(NoPrefixClaim(bot))