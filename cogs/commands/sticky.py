import discord
from discord.ext import commands
import aiosqlite
import datetime
import asyncio
import os
import re

DB_PATH = "db/sticky_messages.db"

class StickyMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sticky_data = {}  # {channel_id: {'type': str, 'data': dict, 'last_msg': Message}}

    async def cog_load(self):
        os.makedirs("db", exist_ok=True)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sticky_messages (
                    channel_id INTEGER PRIMARY KEY,
                    type TEXT,
                    data TEXT
                )
            """)
            await db.commit()

            async with db.execute("SELECT channel_id, type, data FROM sticky_messages") as cursor:
                async for row in cursor:
                    channel_id, msg_type, raw_data = row
                    data = eval(raw_data) if raw_data else {}
                    self.sticky_data[channel_id] = {
                        'type': msg_type,
                        'data': data,
                        'last_msg': None
                    }

    @commands.command(name="setsticky")
    @commands.has_permissions(manage_messages=True)
    async def set_sticky(self, ctx, msg_type: str, *, content: str):
        msg_type = msg_type.lower()
        if msg_type not in ["normal", "embed"]:
            return await ctx.send("❌ Type must be `normal` or `embed`.")

        if msg_type == "normal":
            data = {"text": content}
        else:
            parts = [p.strip() for p in content.split("|") if "=" in p]
            data = {}
            for part in parts:
                try:
                    key, value = part.split("=", 1)
                    data[key.strip().lower()] = value.strip()
                except:
                    continue

            color = data.get("color", "#5865F2").lower()
            if re.match(r"^#?[0-9a-f]{6}$", color.replace("#", "")):
                data["color"] = int(color.replace("#", ""), 16)
            else:
                named_colors = {
                    "blue": 0x3498db,
                    "red": 0xe74c3c,
                    "green": 0x2ecc71,
                    "purple": 0x9b59b6,
                    "yellow": 0xf1c40f,
                    "blurple": 0x5865F2
                }
                data["color"] = named_colors.get(color, 0x5865F2)

        self.sticky_data[ctx.channel.id] = {
            "type": msg_type,
            "data": data,
            "last_msg": None
        }

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "REPLACE INTO sticky_messages (channel_id, type, data) VALUES (?, ?, ?)",
                (ctx.channel.id, msg_type, str(data))
            )
            await db.commit()

        await ctx.send(f"✅ Sticky message set as `{msg_type}` for this channel.")

    @commands.command(name="removesticky")
    @commands.has_permissions(manage_messages=True)
    async def remove_sticky(self, ctx):
        if ctx.channel.id not in self.sticky_data:
            return await ctx.send("⚠ No sticky message is set in this channel.")

        data = self.sticky_data[ctx.channel.id]
        if data.get("last_msg"):
            try:
                await data["last_msg"].delete()
            except:
                pass

        del self.sticky_data[ctx.channel.id]

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM sticky_messages WHERE channel_id = ?", (ctx.channel.id,))
            await db.commit()

        await ctx.send("❌ Sticky message removed.")

    @commands.command(name="stickyconfig")
    @commands.has_permissions(manage_messages=True)
    async def sticky_config(self, ctx):
        data = self.sticky_data.get(ctx.channel.id)
        if not data:
            return await ctx.send("⚠ No sticky message is set in this channel.")

        msg_type = data["type"]
        content = data["data"]

        if msg_type == "normal":
            await ctx.send(f"📝 Sticky Type: `normal`\n📌 Message:\n```{content.get('text', '')}```")
        else:
            embed_preview = discord.Embed(
                title=content.get("title", "No Title"),
                description=content.get("description", "No Description"),
                color=content.get("color", 0x5865F2)
            )
            if "footer" in content:
                embed_preview.set_footer(text=content["footer"])
            if "author" in content:
                embed_preview.set_author(name=content["author"])
            if "image" in content:
                embed_preview.set_image(url=content["image"])
            if "thumbnail" in content:
                embed_preview.set_thumbnail(url=content["thumbnail"])

            await ctx.send(
                content="📄 Sticky Type: `embed` — Here is the current configuration:",
                embed=embed_preview
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        channel_id = message.channel.id
        if channel_id not in self.sticky_data:
            return

        data = self.sticky_data[channel_id]

        await asyncio.sleep(1)

        if data.get("last_msg"):
            try:
                await data["last_msg"].delete()
            except:
                pass

        msg_type = data['type']
        content = data['data']

        if msg_type == "normal":
            msg = await message.channel.send(content.get("text", ""))
        else:
            embed = discord.Embed(
                title=content.get("title"),
                description=content.get("description"),
                color=content.get("color", 0x5865F2)
            )
            if "footer" in content:
                embed.set_footer(text=content["footer"])
            if "author" in content:
                embed.set_author(name=content["author"])
            if "image" in content:
                embed.set_image(url=content["image"])
            if "thumbnail" in content:
                embed.set_thumbnail(url=content["thumbnail"])

            msg = await message.channel.send(embed=embed)

        self.sticky_data[channel_id]['last_msg'] = msg

def setup(bot):
    bot.add_cog(StickyMessage(bot))
