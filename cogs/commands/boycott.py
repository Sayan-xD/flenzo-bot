import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import discord
from discord.ext import commands

log = logging.getLogger(__name__)

DATA_PATH = Path("data/boycott_config.json")


def is_guild_staff():
    """Check: Administrator OR Manage Guild OR guild owner."""
    async def predicate(ctx: commands.Context) -> bool:
        if not ctx.guild:
            return False
        if ctx.author.id == ctx.guild.owner_id:
            return True
        perms = ctx.author.guild_permissions
        return perms.administrator or perms.manage_guild
    return commands.check(predicate)


class JSONStorage:
    """Async-safe JSON storage using a lock and thread I/O for disk operations."""
    def __init__(self, path: Path):
        self.path = path
        self._lock = asyncio.Lock()
        self._data: Dict[str, Any] = {"guilds": {}}

    async def load(self) -> None:
        async with self._lock:
            try:
                if not self.path.parent.exists():
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                if not self.path.exists():
                    self._data = {"guilds": {}}
                    await self._save_locked()
                    return
                def _read():
                    with open(self.path, "r", encoding="utf-8") as f:
                        return json.load(f)
                data = await asyncio.to_thread(_read)
                if isinstance(data, dict):
                    self._data = data
                else:
                    log.warning("Storage file %s did not contain a dict; resetting", self.path)
                    self._data = {"guilds": {}}
                    await self._save_locked()
            except FileNotFoundError:
                self._data = {"guilds": {}}
                await self._save_locked()
            except Exception:
                log.exception("Failed to load storage; starting with empty dataset.")
                self._data = {"guilds": {}}
                await self._save_locked()

    async def _save_locked(self) -> None:
        try:
            def _write(d):
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False, indent=2)
            await asyncio.to_thread(_write, self._data)
        except Exception:
            log.exception("Failed to write storage file %s", self.path)

    async def save(self) -> None:
        async with self._lock:
            await self._save_locked()

    async def _ensure_guild(self, guild_id: int) -> Dict[str, Any]:
        guilds = self._data.setdefault("guilds", {})
        return guilds.setdefault(str(guild_id), {
            "flag_role_ids": [],
            "setup_role_ids": [],
            "log_channel_id": None
        })

    async def get_guild(self, guild_id: int) -> Dict[str, Any]:
        async with self._lock:
            g = await self._ensure_guild(guild_id)
            return {
                "flag_role_ids": list(g.get("flag_role_ids", [])),
                "setup_role_ids": list(g.get("setup_role_ids", [])),
                "log_channel_id": g.get("log_channel_id")
            }

    async def set_flag_roles(self, guild_id: int, role_ids: List[int]) -> None:
        async with self._lock:
            g = await self._ensure_guild(guild_id)
            g["flag_role_ids"] = [str(i) for i in role_ids]
            self._data["guilds"][str(guild_id)] = g
            await self._save_locked()

    async def set_setup_roles(self, guild_id: int, role_ids: List[int]) -> None:
        async with self._lock:
            g = await self._ensure_guild(guild_id)
            g["setup_role_ids"] = [str(i) for i in role_ids]
            self._data["guilds"][str(guild_id)] = g
            await self._save_locked()

    async def set_log_channel(self, guild_id: int, channel_id: Optional[int]) -> None:
        async with self._lock:
            g = await self._ensure_guild(guild_id)
            g["log_channel_id"] = str(channel_id) if channel_id is not None else None
            self._data["guilds"][str(guild_id)] = g
            await self._save_locked()

    async def reset_guild(self, guild_id: int) -> None:
        async with self._lock:
            self._data.setdefault("guilds", {})[str(guild_id)] = {
                "flag_role_ids": [],
                "setup_role_ids": [],
                "log_channel_id": None
            }
            await self._save_locked()


class RoleSelect(discord.ui.Select):
    """Single-selection role select (enforces exactly one selection)."""
    def __init__(self, placeholder: str, options: List[discord.SelectOption]):
        # Exactly one selection required
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        view: "RoleSelectView" = self.view  # type: ignore
        if view is None:
            try:
                await interaction.response.send_message("View state lost.", ephemeral=True)
            except Exception:
                pass
            return
        # store the single selected value
        if self.custom_id == "flag_select":
            view.selected_flag_ids = list(self.values)
        elif self.custom_id == "setup_select":
            view.selected_setup_ids = list(self.values)
        # Acknowledge component interaction so user doesn't see "This interaction failed"
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            # ignore if already deferred
            pass


class RoleSelectView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild: discord.Guild, current_flag_ids: List[str], current_setup_ids: List[str], timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.guild = guild
        # keep only first saved id if existing (we enforce exactly one)
        self.selected_flag_ids: List[str] = list(current_flag_ids[:1])
        self.selected_setup_ids: List[str] = list(current_setup_ids[:1])

        # build options from guild roles (exclude @everyone)
        roles = [r for r in guild.roles if r != guild.default_role]
        roles_sorted = sorted(roles, key=lambda r: r.position, reverse=True)
        self.limit_warning = False
        if len(roles_sorted) > 25:
            roles_sorted = roles_sorted[:25]
            self.limit_warning = True

        flag_options: List[discord.SelectOption] = []
        setup_options: List[discord.SelectOption] = []
        for r in roles_sorted:
            default_flag = str(r.id) in current_flag_ids
            default_setup = str(r.id) in current_setup_ids
            flag_options.append(discord.SelectOption(label=r.name, value=str(r.id), description=f"id: {r.id}", default=default_flag))
            setup_options.append(discord.SelectOption(label=r.name, value=str(r.id), description=f"id: {r.id}", default=default_setup))

        # Add selects only when there are options
        if flag_options:
            flag_select = RoleSelect("Select ONE flag role", flag_options)
            flag_select.custom_id = "flag_select"
            self.add_item(flag_select)
        if setup_options:
            setup_select = RoleSelect("Select ONE setup/protected role", setup_options)
            setup_select.custom_id = "setup_select"
            self.add_item(setup_select)

    @discord.ui.button(label="Save", style=discord.ButtonStyle.success, custom_id="save_btn")
    async def save_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # interaction must be first param; fixed from earlier swapped order
        try:
            flag_ids = [int(self.selected_flag_ids[0])] if self.selected_flag_ids else []
            setup_ids = [int(self.selected_setup_ids[0])] if self.selected_setup_ids else []
            await self.bot.get_cog("Boycott").storage.set_flag_roles(self.guild.id, flag_ids)
            await self.bot.get_cog("Boycott").storage.set_setup_roles(self.guild.id, setup_ids)
            desc = (f"Saved {len(flag_ids)} flag role(s) and {len(setup_ids)} setup role(s).\n"
                    + ("Note: only the first 25 roles were shown for selection." if getattr(self, "limit_warning", False) else ""))
            log.info("Boycott: saved flag_ids=%s setup_ids=%s for guild=%s", flag_ids, setup_ids, self.guild.id)
            # Try to edit original message via interaction response
            try:
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="Configuration saved", description=desc, color=discord.Color.green()), view=None)
            except Exception:
                # Fallback: try editing the interaction.message directly
                try:
                    msg = getattr(interaction, "message", None)
                    if msg:
                        await msg.edit(embed=discord.Embed(title="Configuration saved", description=desc, color=discord.Color.green()), view=None)
                    else:
                        # Final fallback: send ephemeral confirmation
                        await interaction.response.send_message(embed=discord.Embed(title="Configuration saved", description=desc, color=discord.Color.green()), ephemeral=True)
                except Exception:
                    log.exception("Failed to send/save confirmation after saving configuration for guild %s", self.guild.id)
        except Exception:
            log.exception("Failed to save role selections for guild %s", self.guild.id)
            try:
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="Save failed", description="An error occurred while saving configuration.", color=discord.Color.red()), view=None)
            except Exception:
                try:
                    await interaction.response.send_message(embed=discord.Embed(title="Save failed", description="An error occurred while saving configuration.", color=discord.Color.red()), ephemeral=True)
                except Exception:
                    pass

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_btn")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.edit_message(content=None, embed=discord.Embed(title="Cancelled", description="No changes were saved.", color=discord.Color.orange()), view=None)
        except Exception:
            try:
                await interaction.response.send_message(embed=discord.Embed(title="Cancelled", description="No changes were saved.", color=discord.Color.orange()), ephemeral=True)
            except Exception:
                pass

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            msg = getattr(self, "message", None)
            if msg:
                await msg.edit(view=self)
        except Exception:
            pass


class Boycott(commands.Cog):
    """
    Boycott / Voice-guard cog (single-flag + single-protected role per guild).
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.storage = JSONStorage(DATA_PATH)

    # Helpers
    def _embed(self, title: str, description: str, color: discord.Color = discord.Color.blue()) -> discord.Embed:
        return discord.Embed(title=title, description=description, color=color)

    async def _get_config(self, guild_id: int) -> Dict[str, Any]:
        return await self.storage.get_guild(guild_id)

    # Commands
    @commands.group(name="boycott", invoke_without_command=True)
    @commands.guild_only()
    @is_guild_staff()
    async def boycott(self, ctx: commands.Context):
        embed = self._embed(
            "Boycott / Voice-guard",
            "Subcommands: setup, add, remove, log, config, reset\n"
            "Example: boycott setup  — open role-selection dropdowns\n"
            "Then use: boycott add @User  — to give configured flagged role(s) to a user",
            discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @boycott.command(name="setup")
    @commands.guild_only()
    @is_guild_staff()
    async def setup(self, ctx: commands.Context):
        """Interactive setup: choose exactly one flag role and exactly one setup/protected role."""
        cfg = await self._get_config(ctx.guild.id)
        current_flags = cfg.get("flag_role_ids", []) or []
        current_setup = cfg.get("setup_role_ids", []) or []

        view = RoleSelectView(self.bot, ctx.guild, current_flags, current_setup)
        # If no selects were added (no roles), inform user
        if not any(isinstance(ch, discord.ui.Select) for ch in view.children):
            await ctx.send(embed=self._embed("No roles available", "This server has no roles (other than @everyone). Create roles first, then run `boycott setup`.", discord.Color.gold()))
            return
        msg = await ctx.send(embed=self._embed("Select roles", "Select exactly one flag role and exactly one setup/protected role. After selecting, press Save." + ("\n\nNote: only the first 25 roles are shown." if getattr(view, "limit_warning", False) else "")), view=view)
        view.message = msg  # bind for timeout editing

    @boycott.command(name="config")
    @commands.guild_only()
    @is_guild_staff()
    async def config(self, ctx: commands.Context):
        cfg = await self._get_config(ctx.guild.id)
        flag_ids = cfg.get("flag_role_ids", []) or []
        setup_ids = cfg.get("setup_role_ids", []) or []
        ch = cfg.get("log_channel_id")

        def expand_roles(role_ids):
            if not role_ids:
                return "None"
            lines = []
            for rid in role_ids:
                r = ctx.guild.get_role(int(rid))
                if r:
                    lines.append(f"{r.mention} ({rid})")
                else:
                    lines.append(str(rid))
            return "\n".join(lines)

        desc = f"Flag role:\n{expand_roles(flag_ids)}\n\nSetup/protected role:\n{expand_roles(setup_ids)}\n\nLog channel: {('<#'+ch+'>') if ch else 'None'}"
        await ctx.send(embed=self._embed("Boycott Configuration", desc, discord.Color.blue()))

    @boycott.command(name="reset")
    @commands.guild_only()
    @is_guild_staff()
    async def reset(self, ctx: commands.Context):
        await self.storage.reset_guild(ctx.guild.id)
        await ctx.send(embed=self._embed("Reset", "Guild configuration reset to defaults.", discord.Color.green()))

    @boycott.command(name="add")
    @commands.guild_only()
    @is_guild_staff()
    async def add(self, ctx: commands.Context, member: discord.Member):
        """Give the configured flagged role to a member (assign role)."""
        cfg = await self._get_config(ctx.guild.id)
        flag_ids = cfg.get("flag_role_ids", []) or []
        if not flag_ids:
            await ctx.send(embed=self._embed("No flag role(s)", "No flag role configured. Use `boycott setup` first.", discord.Color.gold()))
            return
        roles_to_add = []
        for rid in flag_ids:
            r = ctx.guild.get_role(int(rid))
            if r:
                roles_to_add.append(r)
        if not roles_to_add:
            await ctx.send(embed=self._embed("No valid roles", "Configured flag role was not found in this server. Re-run `boycott setup`.", discord.Color.gold()))
            return
        try:
            await member.add_roles(*roles_to_add, reason=f"Assigned by {ctx.author} via boycott add")
            names = ", ".join(r.mention for r in roles_to_add)
            await ctx.send(embed=self._embed("Role assigned", f"Gave {names} to {member.mention}.", discord.Color.green()))
        except Exception:
            log.exception("Failed to assign flag roles %s to member %s in guild %s", flag_ids, member.id, ctx.guild.id)
            await ctx.send(embed=self._embed("Failed", "Could not assign the role. Check bot role position and Manage Roles permission.", discord.Color.red()))

    @boycott.command(name="remove")
    @commands.guild_only()
    @is_guild_staff()
    async def remove(self, ctx: commands.Context, member: discord.Member):
        """Remove the configured flagged role from a member."""
        cfg = await self._get_config(ctx.guild.id)
        flag_ids = cfg.get("flag_role_ids", []) or []
        if not flag_ids:
            await ctx.send(embed=self._embed("No flag role(s)", "No flag role configured. Use `boycott setup` first.", discord.Color.gold()))
            return
        roles_to_remove = []
        for rid in flag_ids:
            r = ctx.guild.get_role(int(rid))
            if r:
                roles_to_remove.append(r)
        if not roles_to_remove:
            await ctx.send(embed=self._embed("No valid roles", "Configured flag role was not found in this server. Re-run `boycott setup`.", discord.Color.gold()))
            return
        try:
            await member.remove_roles(*roles_to_remove, reason=f"Removed by {ctx.author} via boycott remove")
            names = ", ".join(r.mention for r in roles_to_remove)
            await ctx.send(embed=self._embed("Role removed", f"Removed {names} from {member.mention}.", discord.Color.green()))
        except Exception:
            log.exception("Failed to remove flag roles %s from member %s in guild %s", flag_ids, member.id, ctx.guild.id)
            await ctx.send(embed=self._embed("Failed", "Could not remove the role. Check bot role position and Manage Roles permission.", discord.Color.red()))

    # Log channel commands
    @boycott.group(name="log", invoke_without_command=True)
    @commands.guild_only()
    @is_guild_staff()
    async def log(self, ctx: commands.Context):
        await ctx.send(embed=self._embed("Log commands", "Subcommands: channel set <#channel|id>, channel remove, channel config", discord.Color.blue()))

    @log.group(name="channel", invoke_without_command=True)
    @commands.guild_only()
    @is_guild_staff()
    async def log_channel(self, ctx: commands.Context):
        await ctx.send(embed=self._embed("Log channel", "Subcommands: set <#channel|id>, remove, config", discord.Color.blue()))

    @log_channel.command(name="set")
    @commands.guild_only()
    @is_guild_staff()
    async def log_channel_set(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.storage.set_log_channel(ctx.guild.id, channel.id)
        await ctx.send(embed=self._embed("Log channel set", f"Alerts will be posted in {channel.mention}.", discord.Color.green()))

    @log_channel.command(name="remove")
    @commands.guild_only()
    @is_guild_staff()
    async def log_channel_remove(self, ctx: commands.Context):
        await self.storage.set_log_channel(ctx.guild.id, None)
        await ctx.send(embed=self._embed("Log channel removed", "Alert channel unset.", discord.Color.orange()))

    @log_channel.command(name="config")
    @commands.guild_only()
    @is_guild_staff()
    async def log_channel_config(self, ctx: commands.Context):
        cfg = await self._get_config(ctx.guild.id)
        ch_id = cfg.get("log_channel_id")
        desc = f"<#{ch_id}> ({ch_id})" if ch_id else "Not set"
        await ctx.send(embed=self._embed("Log channel config", desc, discord.Color.blue()))

    # Event listener
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        try:
            guild = member.guild
            old_channel = before.channel
            new_channel = after.channel
            if new_channel is None:
                return  # left voice
            if old_channel and old_channel.id == new_channel.id:
                return  # no movement

            cfg = await self._get_config(guild.id)
            flag_ids = set(cfg.get("flag_role_ids", []) or [])
            setup_ids = set(cfg.get("setup_role_ids", []) or [])
            if not flag_ids or not setup_ids:
                return  # not configured for this guild

            # Is the member flagged? (any configured flag role)
            member_role_ids = {str(r.id) for r in member.roles}
            if not member_role_ids.intersection(flag_ids):
                return

            # Are there any other members in the channel who have the setup role?
            other_members = [m for m in new_channel.members if m.id != member.id]
            trigger_present = False
            for m in other_members:
                if {str(r.id) for r in m.roles}.intersection(setup_ids):
                    trigger_present = True
                    break
            if not trigger_present:
                return

            # Attempt to disconnect the flagged user (move to None)
            disconnect_success = False
            try:
                await member.move_to(None, reason="Flagged user entered protected voice channel")
                disconnect_success = True
                log.info("Disconnected flagged member %s (%s) in guild %s", member.display_name, member.id, guild.id)
            except Exception:
                disconnect_success = False
                log.exception("Failed to disconnect flagged member %s (%s) in guild %s", member.display_name, member.id, guild.id)

            # Use member.mention instead of member.user
            embed = self._embed(
                "Flagged User Disconnected" if disconnect_success else "Flagged User - Disconnect Failed",
                f"Guild: {guild.name} ({guild.id})\nUser: {member.mention} ({member.id})\nChannel: {new_channel.name} ({new_channel.id})\nAction: {'Disconnected' if disconnect_success else 'Disconnect failed (insufficient permissions)'}",
                discord.Color.red()
            )

            # Send only to configured log channel for THIS guild
            sent = False
            ch_id = cfg.get("log_channel_id")
            if ch_id:
                try:
                    ch = guild.get_channel(int(ch_id))
                except Exception:
                    ch = None
                if not ch:
                    log.warning("Boycott: configured log channel %s not found in guild %s", ch_id, guild.id)
                else:
                    perms = ch.permissions_for(guild.me)
                    if perms.send_messages:
                        try:
                            await ch.send(embed=embed)
                            sent = True
                        except Exception:
                            log.exception("Failed to send embed to log channel %s in guild %s", ch_id, guild.id)
                    else:
                        log.warning("Bot lacks send_messages in log channel %s for guild %s", ch_id, guild.id)
            if not sent:
                log.warning("No usable log channel set or send failed for guild %s; alert not delivered. Configure a log channel with `boycott log channel set`.", guild.id)
        except Exception:
            log.exception("Error in on_voice_state_update handler for guild %s", getattr(member.guild, "id", "unknown"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Boycott(bot))