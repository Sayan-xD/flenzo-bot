
import asyncio
import os
import sys
import logging
from discord.ext import commands, tasks

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s'
)

RESTART_CHANNEL_ID = 1389300355988197576  # 🔁 Replace with your log channel ID


class AutoRestart(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_restart.start()
        logger.info("AutoRestart cog initialized.")

    @tasks.loop(minutes=10)
    async def auto_restart(self):
        try:
            channel = self.bot.get_channel(RESTART_CHANNEL_ID)
            if channel:
                await channel.send("🔁 Bot is restarting automatically...")

            logger.info("Bot restarting now...")
            await self.bot.close()
            os.execv(sys.executable, [sys.executable] + sys.argv)

        except Exception as e:
            logger.exception("Auto-restart failed!")
            channel = self.bot.get_channel(RESTART_CHANNEL_ID)
            if channel:
                try:
                    await channel.send(f"❌ Failed to restart the bot: `{e}`")
                except Exception as send_error:
                    logger.error(f"Failed to send error message to channel: {send_error}")

    @auto_restart.before_loop
    async def before_auto_restart(self):
        await self.bot.wait_until_ready()
        logger.info("AutoRestart task waiting for bot to be ready.")

    @commands.group(name="autorestart", invoke_without_command=True)
    async def autorestart_group(self, ctx):
        """Manage the AutoRestart feature."""
        await ctx.send("⚙ Use `!autorestart enable` or `!autorestart disable`")

    @autorestart_group.command(name="enable")
    @commands.is_owner()
    async def enable_autorestart(self, ctx):
        if self.auto_restart.is_running():
            await ctx.send("✅ Auto-restart is already enabled.")
        else:
            self.auto_restart.start()
            await ctx.send("✅ Auto-restart has been enabled.")
            logger.info("AutoRestart manually enabled.")

    @autorestart_group.command(name="disable")
    @commands.is_owner()
    async def disable_autorestart(self, ctx):
        if self.auto_restart.is_running():
            self.auto_restart.cancel()
            await ctx.send("⛔ Auto-restart has been disabled.")
            logger.info("AutoRestart manually disabled.")
        else:
            await ctx.send("⚠ Auto-restart is already disabled.")

async def setup(bot):
    await bot.add_cog(AutoRestart(bot))
    logger.info("AutoRestart cog loaded.")
