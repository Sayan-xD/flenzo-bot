import discord
from discord.ext import commands, tasks
import datetime, pytz, time as t
import random
import typing
import asyncio
import logging
import os
import aiohttp
import json

DATA_PATH = "giveaway_data.json"

def time_convert(time: str):
    pos = ["s", "m", "h", "d"]
    time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400, "f": 259200}
    unit = time[-1]
    if unit not in pos:
        return -1
    try:
        val = int(time[:-1])
    except ValueError:
        return -2
    return val * time_dict[unit]

def utcnow():
    # returns timezone-aware UTC datetime
    return datetime.datetime.now(pytz.UTC)

def load_data():
    if not os.path.exists(DATA_PATH):
        with open(DATA_PATH, "w") as f:
            json.dump({
                "giveaways": [],
                "giveaway_managers": {},
                "giveaway_manager_roles": {}
            }, f)
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=4)

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(DATA_PATH):
            save_data({
                "giveaways": [],
                "giveaway_managers": {},
                "giveaway_manager_roles": {}
            })
        self.GiveawayEnd.start()

    async def cog_load(self):
        await self.check_for_ended_giveaways()

    async def cog_unload(self):
        self.GiveawayEnd.cancel()

    async def is_giveaway_manager(self, guild_id: int, user: discord.Member):
        """
        Return True if:
        - user has administrator OR manage_guild permission
        OR
        - user is listed in giveaway_managers for this guild
        OR
        - user has a role listed in giveaway_manager_roles for this guild

        Important: explicit manager entries (user or role) bypass the permission requirement.
        """
        # If user has server-level power, allow
        if getattr(user, "guild_permissions", None):
            if user.guild_permissions.administrator or user.guild_permissions.manage_guild:
                return True

        # Load JSON data and check explicit lists/roles
        data = load_data()
        str_gid = str(guild_id)

        # Check explicit user managers (these bypass permissions)
        gw_managers = data.get("giveaway_managers", {})
        if str_gid in gw_managers:
            # JSON stores user IDs as ints; ensure comparison uses int
            try:
                stored_users = [int(x) for x in gw_managers.get(str_gid, [])]
            except Exception:
                stored_users = gw_managers.get(str_gid, [])
            if user.id in stored_users:
                return True

        # Check explicit role managers (these bypass permissions)
        gw_role_managers = data.get("giveaway_manager_roles", {})
        if str_gid in gw_role_managers:
            try:
                stored_roles = [int(x) for x in gw_role_managers.get(str_gid, [])]
            except Exception:
                stored_roles = gw_role_managers.get(str_gid, [])
            # Ensure roles on the member are checked
            for role_id in stored_roles:
                role_obj = user.guild.get_role(role_id)
                if role_obj and role_obj in user.roles:
                    return True

        return False

    async def check_for_ended_giveaways(self):
        now_ts = int(utcnow().timestamp())
        data = load_data()
        ended_gws = [gw for gw in data.get("giveaways", []) if int(gw.get("ends_at", 0)) <= now_ts]
        for gw in ended_gws:
            await self.end_giveaway(gw)

    async def end_giveaway(self, giveaway):
        try:
            current_time = int(utcnow().timestamp())
            guild = self.bot.get_guild(int(giveaway["guild_id"]))
            if guild is None:
                self.delete_giveaway(giveaway["message_id"])
                return

            channel = self.bot.get_channel(int(giveaway["channel_id"]))
            if channel is None:
                self.delete_giveaway(giveaway["message_id"])
                return

            try:
                message = await channel.fetch_message(int(giveaway["message_id"]))
            except discord.NotFound:
                self.delete_giveaway(giveaway["message_id"])
                return
            except aiohttp.ClientResponseError as e:
                if getattr(e, "status", None) == 503:
                    await asyncio.sleep(2)
                    try:
                        message = await channel.fetch_message(int(giveaway["message_id"]))
                    except Exception:
                        self.delete_giveaway(giveaway["message_id"])
                        return
                else:
                    logging.error(f"Error ending giveaway: {e}")
                    return

            target_emoji = "<a:giveaway:1380910108606992506>"
            reaction = next((r for r in message.reactions if str(r.emoji) == target_emoji), None)
            if not reaction:
                await message.reply(
                    f"No one won the **{giveaway['prize']}** giveaway, due to Not enough participants."
                )
                self.delete_giveaway(giveaway["message_id"])
                return

            users = [u.id async for u in reaction.users()]
            if self.bot.user.id in users:
                users.remove(self.bot.user.id)
            if len(users) < 1:
                await message.reply(
                    f"No one won the **{giveaway['prize']}** giveaway, due to Not enough participants."
                )
                self.delete_giveaway(giveaway["message_id"])
                return

            winners_count = min(len(users), int(giveaway["winners"]))
            winner_ids = random.sample(users, k=winners_count)
            winner_mentions = ', '.join(f'<@!{i}>' for i in winner_ids)

            embed = discord.Embed(
                title=f"{giveaway['prize']}",
                description=(
                    f"<a:dot_yellow:1392786864741683344> Ended at <t:{current_time}:R>\n"
                    f"<a:dot_yellow:1392786864741683344> Hosted by <@{int(giveaway['host_id'])}>\n"
                    f"<a:dot_yellow:1392786864741683344> Winner(s): {winner_mentions}"
                ),
                color=0xFFF700
            )
            embed.timestamp = datetime.datetime.fromtimestamp(current_time, tz=datetime.timezone.utc)
            embed.set_thumbnail(url="")
            embed.set_footer(text="Ended at")
            await message.edit(content="<:ended:1380911223650127954> **GIVEAWAY ENDED** <:ended:1380911223650127954>", embed=embed)

            # Announcement (plain text as requested)
            await message.reply(
                f"<a:giveaway:1380910108606992506> Congrats {winner_mentions}, you won **{giveaway['prize']}!**, Hosted by <@{int(giveaway['host_id'])}>"
            )
            self.delete_giveaway(giveaway["message_id"])
        except Exception as e:
            logging.error(f"Error ending giveaway: {e}")
            try:
                self.delete_giveaway(giveaway.get("message_id"))
            except Exception:
                pass

    def delete_giveaway(self, message_id: int):
        data = load_data()
        data["giveaways"] = [gw for gw in data.get("giveaways", []) if gw.get("message_id") != message_id]
        save_data(data)

    @tasks.loop(seconds=5)
    async def GiveawayEnd(self):
        await self.check_for_ended_giveaways()

    def manager_check():
        async def predicate(ctx):
            cog = ctx.bot.get_cog("Giveaway")
            if not cog:
                return False
            return await cog.is_giveaway_manager(ctx.guild.id, ctx.author)
        return commands.check(predicate)

    # Cog-level command error handler:
    # This ensures that when a user lacks required permissions (CheckFailure),
    # they receive a friendly message. It also covers alias invocations.
    async def cog_command_error(self, ctx, error):
        # Only handle permission/check failures for this cog's commands
        if isinstance(error, commands.CheckFailure):
            try:
                embed = discord.Embed(
                    title="⛔ Permission denied",
                    description=(
                        "You need the Manage Server permission or be a configured Giveaway Manager "
                        "to use this command."
                    ),
                    color=0xFFCC00
                )
                await ctx.reply(embed=embed)
            except Exception:
                pass
            return
        # For other errors, let them bubble up (or handle/log as needed)
        # You can log unexpected errors here:
        if not isinstance(error, commands.CommandNotFound):
            logging.debug(f"Unhandled error in Giveaway cog: {error}")

    @commands.hybrid_group(name="giveaway", invoke_without_command=True, aliases=["gw"])
    async def giveaway(self, ctx):
        embed = discord.Embed(
            title="Giveaway Commands [6]",
            description="<> Duty | [] Optional",
            color=0xFFF700
        )
        embed.add_field(
            name="giveaway start",
            value="Starts a new giveaway.\nUsage: `giveaway start <duration> <winners> <prize>`",
            inline=False
        )
        embed.add_field(
            name="giveaway end",
            value="Ends a giveaway before its ending time.\nUsage: `giveaway end [message_id]` (or reply to the giveaway message)",
            inline=False
        )
        embed.add_field(
            name="giveaway reroll",
            value="Rerolls a giveaway on replying the giveaway ended message.\nUsage: `giveaway reroll` (reply to ended message)",
            inline=False
        )
        embed.add_field(
            name="giveaway list",
            value="Lists all ongoing giveaways.\nUsage: `giveaway list`",
            inline=False
        )
        embed.add_field(
            name="giveaway manager add/remove/list",
            value=(
                "Manage giveaway managers (user/role).\n"
                "Usage:\n"
                "`giveaway manager add @user`\n"
                "`giveaway manager addrole @role`\n"
                "`giveaway manager remove @user`\n"
                "`giveaway manager removerole @role`\n"
                "`giveaway manager list`"
            ),
            inline=False
        )
        await ctx.reply(embed=embed)

    @giveaway.command(name="start", aliases=["gstart"])
    @manager_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def giveaway_start(self, ctx, time, winners: int, *, prize: str):
        data = load_data()
        ongoing = len([gw for gw in data.get("giveaways", []) if int(gw.get("guild_id", 0)) == ctx.guild.id])
        if winners >= 15:
            embed = discord.Embed(title="⚠️ Access Denied", description="Cannot exceed more than 15 winners.", color=0xFFF700)
            msg = await ctx.reply(embed=embed)
            await asyncio.sleep(5)
            await msg.delete()
            return

        if ongoing >= 10:
            embed = discord.Embed(title="⚠️ Access Denied", description="You can only host up to 10 giveaways in this Guild.", color=0xFFF700)
            msg = await ctx.reply(embed=embed)
            await asyncio.sleep(5)
            await msg.delete()
            return

        converted = time_convert(time)
        if converted == -1 or converted == -2 or converted / 60 >= 44640:
            err = "Invalid time format" if converted in (-1, -2) else "Time cannot exceed 31 days!"
            embed = discord.Embed(title="❌ Error", description=err, color=0xFFF700)
            msg = await ctx.reply(embed=embed)
            await asyncio.sleep(5)
            await msg.delete()
            return

        now_utc = int(utcnow().timestamp())
        ends_at = now_utc + converted
        embed = discord.Embed(
            title=f"<a:gift:1380912449149997056> {prize} <a:gift:1380912449149997056>",
            description=(
                f"<a:dot_yellow:1392786864741683344> Winner(s): **{winners}**\n"
                f"<a:dot_yellow:1392786864741683344> React with <a:giveaway:1380910108606992506> to participate!\n"
                f"<a:dot_yellow:1392786864741683344> Ends <t:{ends_at}:R> (<t:{ends_at}:f>)\n"
                f"\n<a:dot_yellow:1392786864741683344> Hosted by {ctx.author.mention}"
            ),
            color=0xFFF700
        )
        embed.timestamp = datetime.datetime.fromtimestamp(ends_at, tz=datetime.timezone.utc)
        embed.set_thumbnail(url="")
        footer_icon = getattr(ctx.bot.user, "avatar", None)
        icon_url = footer_icon.url if footer_icon else None
        embed.set_footer(text="Ends at", icon_url=icon_url)
        message = await ctx.reply("<a:giveaway:1380910108606992506> **GIVEAWAY** <a:giveaway:1380910108606992506>", embed=embed)
        try:
            await ctx.message.delete()
        except Exception:
            pass
        data.setdefault("giveaways", []).append({
            "guild_id": ctx.guild.id,
            "host_id": ctx.author.id,
            "start_time": now_utc,
            "ends_at": ends_at,
            "prize": prize,
            "winners": winners,
            "message_id": message.id,
            "channel_id": ctx.channel.id
        })
        save_data(data)
        await message.add_reaction("<a:giveaway:1380910108606992506>")

    @giveaway.command(name="end", aliases=["gend"])
    @manager_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def giveaway_end(self, ctx, message_id: typing.Optional[int] = None):
        data = load_data()
        if message_id:
            try:
                message_id = int(message_id)
            except ValueError:
                embed = discord.Embed(title="⚠️ Access Denied", description="Invalid message ID provided.", color=0xFFF700)
                msg = await ctx.reply(embed=embed)
                await asyncio.sleep(5)
                await msg.delete()
                return

        gw = None
        if message_id:
            gw = next((x for x in data.get("giveaways", []) if x.get("message_id") == message_id), None)
        elif ctx.message.reference:
            ref_res = ctx.message.reference.resolved
            if ref_res:
                ref_id = ref_res.id
                gw = next((x for x in data.get("giveaways", []) if x.get("message_id") == ref_id), None)
                message_id = ref_id

        if not gw:
            embed = discord.Embed(title="❌ Error", description="The giveaway was not found.", color=0x000000)
            msg = await ctx.reply(embed=embed)
            await asyncio.sleep(5)
            await msg.delete()
            return

        ch = self.bot.get_channel(int(gw["channel_id"]))
        message = await ch.fetch_message(int(message_id))
        target_emoji = "<a:giveaway:1380910108606992506>"
        reaction = next((r for r in message.reactions if str(r.emoji) == target_emoji), None)
        if not reaction:
            await ctx.reply(
                f"✅ Successfully Ended the giveaway in <#{int(gw['channel_id'])}>"
            )
            await message.reply(
                f"No one won the **{gw['prize']}** giveaway, due to Not enough participants."
            )
            self.delete_giveaway(message_id)
            return

        users = [u.id async for u in reaction.users()]
        if self.bot.user.id in users:
            users.remove(self.bot.user.id)
        if len(users) < 1:
            await ctx.reply(
                f"✅ Successfully Ended the giveaway in <#{int(gw['channel_id'])}>"
            )
            await message.reply(
                f"No one won the **{gw['prize']}** giveaway, due to Not enough participants."
            )
            self.delete_giveaway(message_id)
            return

        winner_ids = random.sample(users, k=int(gw["winners"]))
        winner_mentions = ', '.join(f'<@!{i}>' for i in winner_ids)
        current_time = int(utcnow().timestamp())
        embed = discord.Embed(
            title=f"<a:gift:1380912449149997056> {gw['prize']}",
            description=(
                f"<a:dot_yellow:1392786864741683344> Ended at <t:{current_time}:R>\n"
                f"<a:dot_yellow:1392786864741683344> Hosted by <@{int(gw['host_id'])}>\n"
                f"<a:dot_yellow:1392786864741683344> Winner(s): {winner_mentions}"
            ),
            color=0xFFF700
        )
        embed.timestamp = datetime.datetime.fromtimestamp(current_time, tz=datetime.timezone.utc)
        embed.set_thumbnail(url="")
        embed.set_footer(text="Ended")
        await message.edit(content="<a:gift2:1392786541931135018> **GIVEAWAY ENDED** <a:gift2:1392786541931135018>", embed=embed)
        if int(ctx.channel.id) != int(gw["channel_id"]):
            await ctx.reply(
                f"✅ Successfully ended the giveaway in <#{int(gw['channel_id'])}>"
            )
        await message.reply(
            f"<a:giveaway:1380910108606992506> Congrats {winner_mentions}, you won **{gw['prize']}!**, Hosted by <@{int(gw['host_id'])}>"
        )
        self.delete_giveaway(message_id)

    @giveaway.command(name="reroll", aliases=["greroll"])
    @manager_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def giveaway_reroll(self, ctx, message_id: typing.Optional[int] = None):
        data = load_data()
        if not ctx.message.reference:
            msg = await ctx.reply(
                "Reply this command with the Giveaway Ended message to reroll."
            )
            await asyncio.sleep(5)
            await msg.delete()
            return

        message_id = ctx.message.reference.resolved.id
        message = await ctx.fetch_message(message_id)
        if ctx.message.reference.resolved.author.id != self.bot.user.id:
            msg = await ctx.reply(
                "The giveaway was not found."
            )
            await asyncio.sleep(5)
            await msg.delete()
            return

        running = next((x for x in data.get("giveaways", []) if x.get("message_id") == message.id), None)
        if running:
            msg = await ctx.reply(
                "The giveaway is currently running. Please use the `end` command instead to end the giveaway."
            )
            await asyncio.sleep(5)
            await msg.delete()
            return

        target_emoji = "<a:giveaway:1380910108606992506>"
        reaction = next((r for r in message.reactions if str(r.emoji) == target_emoji), None)
        if not reaction:
            await message.reply("No valid participants for reroll.")
            return

        users = [u.id async for u in reaction.users()]
        if self.bot.user.id in users:
            users.remove(self.bot.user.id)
        if len(users) < 1:
            await message.reply("No valid participants for reroll.")
            return

        winner = random.choice(users)
        await message.reply(
            f"<a:giveaway:1380910108606992506> The new winner is <@{winner}>. Congratulations!"
        )

    @giveaway.command(name="list", aliases=["glist"])
    @manager_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def giveaway_list(self, ctx):
        data = load_data()
        giveaways = [gw for gw in data.get("giveaways", []) if int(gw.get("guild_id", 0)) == ctx.guild.id]
        embed = discord.Embed(title="Ongoing Giveaways", color=0xFFF700)
        found = False
        for gw in giveaways:
            found = True
            ends_at = int(gw["ends_at"])
            embed.add_field(
                name=gw["prize"],
                value=(
                    f"Ends: <t:{ends_at}:R> (<t:{ends_at}:f>)\n"
                    f"Winners: {gw['winners']}\n"
                    f"[Jump to Message](https://discord.com/channels/{ctx.guild.id}/{gw['channel_id']}/{gw['message_id']})"
                ),
                inline=False
            )
        if not found:
            embed = discord.Embed(description="No ongoing giveaways.", color=0xFFF700)
        await ctx.reply(embed=embed)

    @giveaway.group(name="manager", invoke_without_command=True, aliases=["managers"])
    async def giveaway_manager(self, ctx):
        em = discord.Embed(title="Giveaway Manager Help", color=0xFFF700,
            description="Subcommands: add, addrole, remove, removerole, list")
        await ctx.reply(embed=em)

    @giveaway_manager.command(name="add", aliases=["adduser"])
    @commands.has_guild_permissions(administrator=True)
    async def giveaway_manager_add_user(self, ctx, member: discord.Member):
        data = load_data()
        str_gid = str(ctx.guild.id)
        if str_gid not in data["giveaway_managers"]:
            data["giveaway_managers"][str_gid] = []
        if member.id in data["giveaway_managers"][str_gid]:
            embed = discord.Embed(color=0xFFF700, description=f"{member.mention} is already a giveaway manager.")
            await ctx.reply(embed=embed)
            return
        data["giveaway_managers"][str_gid].append(member.id)
        save_data(data)
        embed = discord.Embed(color=0xFFF700, description=f"Added {member.mention} as a giveaway manager!")
        await ctx.reply(embed=embed)

    @giveaway_manager.command(name="addrole")
    @commands.has_guild_permissions(administrator=True)
    async def giveaway_manager_add_role(self, ctx, role: discord.Role):
        data = load_data()
        str_gid = str(ctx.guild.id)
        if str_gid not in data["giveaway_manager_roles"]:
            data["giveaway_manager_roles"][str_gid] = []
        if role.id in data["giveaway_manager_roles"][str_gid]:
            embed = discord.Embed(color=0xFFF700, description=f"{role.mention} is already a giveaway manager role.")
            await ctx.reply(embed=embed)
            return
        data["giveaway_manager_roles"][str_gid].append(role.id)
        save_data(data)
        embed = discord.Embed(color=0xFFF700, description=f"Added {role.mention} as a giveaway manager role!")
        await ctx.reply(embed=embed)

    @giveaway_manager.command(name="remove", aliases=["removeuser"])
    @commands.has_guild_permissions(administrator=True)
    async def giveaway_manager_remove_user(self, ctx, member: discord.Member):
        data = load_data()
        str_gid = str(ctx.guild.id)
        if str_gid in data["giveaway_managers"] and member.id in data["giveaway_managers"][str_gid]:
            data["giveaway_managers"][str_gid].remove(member.id)
            save_data(data)
            embed = discord.Embed(color=0xFFF700, description=f"Removed {member.mention} from giveaway managers.")
        else:
            embed = discord.Embed(color=0xFFF700, description=f"{member.mention} is not a giveaway manager.")
        await ctx.reply(embed=embed)

    @giveaway_manager.command(name="removerole")
    @commands.has_guild_permissions(administrator=True)
    async def giveaway_manager_remove_role(self, ctx, role: discord.Role):
        data = load_data()
        str_gid = str(ctx.guild.id)
        if str_gid in data["giveaway_manager_roles"] and role.id in data["giveaway_manager_roles"][str_gid]:
            data["giveaway_manager_roles"][str_gid].remove(role.id)
            save_data(data)
            embed = discord.Embed(color=0xFFF700, description=f"Removed {role.mention} from giveaway manager roles.")
        else:
            embed = discord.Embed(color=0xFFF700, description=f"{role.mention} is not a giveaway manager role.")
        await ctx.reply(embed=embed)

    @giveaway_manager.command(name="list", aliases=["listmanagers"])
    async def giveaway_manager_list(self, ctx):
        data = load_data()
        str_gid = str(ctx.guild.id)
        user_ids = data["giveaway_managers"].get(str_gid, [])
        role_ids = data["giveaway_manager_roles"].get(str_gid, [])
        em = discord.Embed(title="Giveaway Managers", color=0xFFF700)
        if user_ids:
            em.add_field(name="Users", value=", ".join(f"<@{uid}>" for uid in user_ids), inline=False)
        if role_ids:
            em.add_field(name="Roles", value=", ".join(f"<@&{rid}>" for rid in role_ids), inline=False)
        if not user_ids and not role_ids:
            em.description = "No giveaway managers set."
        await ctx.reply(embed=em)

    @commands.Cog.listener("on_message_delete")
    async def GiveawayMessageDelete(self, message):
        if message.author != self.bot.user or not message.guild:
            return
        self.delete_giveaway(message.id)