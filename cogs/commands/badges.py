from discord.ext import commands
import discord
import sqlite3

SUCCESS = "<:IconTick:1381245157759782975>"
ERROR = "<:icon_cross:1381448030481547315>"

BADGE_DISPLAY = {
    "developer": "**<:Developer:1397197858389889047> | Developer**",
    "owner": "**<:gold_owner:1389297086704521226> | Owner**",
    "manager": "**<:Mod:1397197884373340196> | Manager**",
    "admin": "**<:Admin:1397197880682348564> | Admin**",
    "mod": "**<:MekoModeration:1397202355451334746> | Mod**",
    "support": "**<:Supportteam:1397197887456280667> | Support Team**",
    "bug": "**<:BugHunter:1397197889658290266> | Bug Hunter**",
    "premium": "**<a:diamondspin:1397260499716149449> | Premium Users**",
    "friend": "**<:Friend:1397202129483075756> | Friends**",
    "user": "**<:users:1397203631219933226> | Member**"
}

conn = sqlite3.connect('db/badges.db')
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS badges (user_id INTEGER PRIMARY KEY)")
conn.commit()

def add_badge(user_id, badge):
    try:
        c.execute(f"SELECT {badge} FROM badges WHERE user_id = ?", (user_id,))
    except sqlite3.OperationalError:
        c.execute(f"ALTER TABLE badges ADD COLUMN {badge} INTEGER DEFAULT 0")
        conn.commit()
        c.execute(f"SELECT {badge} FROM badges WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result is None:
        c.execute(f"INSERT OR IGNORE INTO badges (user_id, {badge}) VALUES (?, 1)", (user_id,))
    elif result[0] == 0:
        c.execute(f"UPDATE badges SET {badge} = 1 WHERE user_id = ?", (user_id,))
    else:
        return False
    conn.commit()
    return True

def remove_badge(user_id, badge):
    try:
        c.execute(f"SELECT {badge} FROM badges WHERE user_id = ?", (user_id,))
    except sqlite3.OperationalError:
        return False
    result = c.fetchone()
    if result and result[0] == 1:
        c.execute(f"UPDATE badges SET {badge} = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
    return False

class Badges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["profile", "pr"])
    async def badges(self, ctx, member: discord.Member = None):
        processing = await ctx.send("⌛ Loading your profile...")
        member = member or ctx.author
        user_id = member.id

        c.execute("SELECT * FROM badges WHERE user_id = ?", (user_id,))
        badges = c.fetchone()
        if badges:
            badges = dict(zip([col[0] for col in c.description], badges))
        else:
            badges = {k: 0 for k in BADGE_DISPLAY}
            badges["user"] = 1  # Default to Members badge if none

        embed = discord.Embed(title=f"{member.display_name}'s Profile", color=0x000000)
        embed.set_thumbnail(url=member.display_avatar.url)

        # User badges (Discord public flags)
        user_flags = member.public_flags
        user_badges = []

        badge_map = {
            "staff": "**<:DiscordStaff:1324013450707603456> | Discord Employee**",
            "partner": "**<:DiscordPartner:1324013532282622126> | | Partnered Server Owner**",
            "bug_hunter": "**<:BUG_HUNTER_LEVEL_1:1294960972473171972> | Bug Hunter**",
            "hypesquad": "**<:hypesquad_events:1294960968161427527> | HypeSquad Member**",
            "hypesquad_bravery": "**<:Bravery:1385619088256139335> | Bravery**",
            "hypesquad_brilliance": "**<:Briliance:1385617842002464919> | Brilliance**",
            "hypesquad_balance": "**<:Balance:1385617864471482579> | Balance**",
            "early_supporter": "**<:suppoter:1294980752840327168> | Early Supporter**",
            "active_developer": "**<:activedev:1385620819887001781> |  Active Developer**"
        }

        for flag, emoji in badge_map.items():
            if getattr(user_flags, flag, False):
                user_badges.append(emoji)

        user = await self.bot.fetch_user(member.id)
        if user.banner or (user.avatar and user.avatar.is_animated()):
            user_badges.append("**<:Subscriber_Nitro:1385617601597804575> | Nitro Subscriber**")

        for g in self.bot.guilds:
            if g.premium_subscription_count > 0 and member in g.premium_subscribers:
                user_badges.append("**<:icon_booster:1381451121654104155> | Server Booster**")

        embed.add_field(name="__User Badges__", value="\n".join(user_badges) if user_badges else "None", inline=False)

        bot_badges = [BADGE_DISPLAY[k] for k in BADGE_DISPLAY if badges.get(k, 0) == 1]
        if not bot_badges:
            bot_badges = [BADGE_DISPLAY["user"]]
        embed.add_field(name="__Bot Badges__", value="\n".join(bot_badges), inline=False)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        await processing.delete()

    @commands.group(name="bdg", invoke_without_command=True)
    @commands.is_owner()
    async def bdg(self, ctx):
        await ctx.send("Use `bdg add` or `bdg remove`.")

    @bdg.command(name="add")
    @commands.is_owner()
    async def bdg_add(self, ctx, member: discord.Member = None, badge: str = None):
        if member is None or badge is None:
            return await ctx.send(f"{ERROR} Usage: `.bdg add @user badge` or `.bdg add @user all`")

        badge = badge.lower()

        if badge == "all":
            count = 0
            for key in BADGE_DISPLAY:
                if add_badge(member.id, key):
                    count += 1
            return await ctx.send(embed=discord.Embed(
                description=f"{SUCCESS} All `{count}` badges added to {member.mention}.",
                color=0x00ff00
            ))

        if badge not in BADGE_DISPLAY:
            return await ctx.send(embed=discord.Embed(
                description=f"{ERROR} Invalid badge `{badge}`. Please check the badge name.",
                color=0xff0000
            ))

        if add_badge(member.id, badge):
            embed = discord.Embed(description=f"{SUCCESS} Badge `{badge}` added to {member.mention}.", color=0x00ff00)
        else:
            embed = discord.Embed(description=f"{ERROR} {member.mention} already has the `{badge}` badge.", color=0xff0000)
        await ctx.send(embed=embed)

    @bdg.command(name="remove")
    @commands.is_owner()
    async def bdg_remove(self, ctx, member: discord.Member = None, badge: str = None):
        if member is None or badge is None:
            return await ctx.send(f"{ERROR} Usage: `.bdg remove @user badge` or `.bdg remove @user all`")

        badge = badge.lower()

        if badge == "all":
            count = 0
            for key in BADGE_DISPLAY:
                if remove_badge(member.id, key):
                    count += 1
            return await ctx.send(embed=discord.Embed(
                description=f"{SUCCESS} All `{count}` badges removed from {member.mention}.",
                color=0xff0000
            ))

        if badge not in BADGE_DISPLAY:
            return await ctx.send(embed=discord.Embed(
                description=f"{ERROR} Invalid badge `{badge}`. Please check the badge name.",
                color=0xff0000
            ))

        if remove_badge(member.id, badge):
            embed = discord.Embed(description=f"{SUCCESS} Badge `{badge}` removed from {member.mention}.", color=0x00ff00)
        else:
            embed = discord.Embed(description=f"{ERROR} {member.mention} does not have the `{badge}` badge.", color=0xff0000)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Badges(bot))