import discord
import time
import json
from discord.ext import commands
import aiosqlite
from cogs.commands.premium import is_premium

# Local parser function (formerly from utils.embedparser)
async def to_object(msg: str):
    try:
        data = json.loads(msg)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {"content": msg}

class JoinDM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'db/joindm.db'
        self.bot.loop.create_task(self.setup_database())

    async def setup_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS joindm (
                    guild_id INTEGER PRIMARY KEY,
                    message TEXT
                )
            """)
            await db.commit()

    async def get_message(self, guild_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT message FROM joindm WHERE guild_id = ?", (guild_id,))
            row = await cursor.fetchone()
            return row[0] if row else None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        msg = await self.get_message(member.guild.id)
        if not msg:
            return

        z = msg.replace('{user}', f'{member}')\
                .replace('{user.name}', f'{member.name}')\
                .replace('{user.mention}', f'{member.mention}')\
                .replace('{user.avatar}', member.avatar.url if member.avatar else '')\
                .replace('{user.joined_at}', f'<t:{int(member.created_at.timestamp())}:R>')\
                .replace('{user.discriminator}', f'{member.discriminator}')\
                .replace('{guild.name}', f'{member.guild.name}')\
                .replace('{guild.count}', f'{member.guild.member_count}')\
                .replace('{guild.icon}', member.guild.icon.url if member.guild.icon else '')\
                .replace('{guild.id}', f'{member.guild.id}')

        x = await to_object(z)
        try:
            channel = member.dm_channel or await member.create_dm()
            time.sleep(3)
            await channel.send(**x)
        except:
            pass

    @commands.group(name="joindm",  invoke_without_command=True, help="Shows all JoinDM commands.")
    async def joindm(self, ctx):
        embed = discord.Embed(title="JoinDM [5]", description="< > Duty | [ ] Optional", color=0x2f3136)
        embed.add_field(name="➜ joindm message <message>", value="Set the message that will be sent in DM when a member joins.", inline=False)
        embed.add_field(name="➜ joindm config", value="Show the current JoinDM configuration.", inline=False)
        embed.add_field(name="➜ joindm variables", value="List all available JoinDM variables.", inline=False)
        embed.add_field(name="➜ joindm delete", value="Delete the current JoinDM config.", inline=False)
        embed.add_field(name="➜ joindm test", value="Test the current JoinDM message.", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        await ctx.reply(embed=embed, mention_author=False)

    @joindm.command(help="Set the JoinDM message.")
    async def message(self, ctx, *, msg):
        if not ctx.author.guild_permissions.manage_guild:
            embed = discord.Embed(color=0x2f3136, description="⚠️ Missing permission: **Manage Guild**")
            return await ctx.reply(embed=embed, mention_author=False)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("REPLACE INTO joindm (guild_id, message) VALUES (?, ?)", (ctx.guild.id, msg))
            await db.commit()

        embed = discord.Embed(description=f"✅ Set JoinDM message to `{msg}`", color=0x2f3136)
        await ctx.reply(embed=embed, mention_author=False)

    @joindm.command(help="Show the current JoinDM config.")
    async def config(self, ctx):
        if not ctx.author.guild_permissions.manage_guild:
            embed = discord.Embed(color=0x2f3136, description="⚠️ Missing permission: **Manage Guild**")
            return await ctx.reply(embed=embed, mention_author=False)

        msg = await self.get_message(ctx.guild.id)
        embed = discord.Embed(title="JoinDM Configuration", color=0x2f3136)
        embed.add_field(name="Message", value=f"`{msg}`" if msg else "Not set")
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        await ctx.reply(embed=embed, mention_author=False)

    @joindm.command(help="List available JoinDM variables.")
    async def variables(self, ctx):
        embed = discord.Embed(title="JoinDM Variables", color=0x2f3136)
        embed.add_field(name="Member", value="{user}\n{user.name}\n{user.mention}\n{user.avatar}\n{user.discriminator}\n{user.joined_at}", inline=False)
        embed.add_field(name="Guild", value="{guild.name}\n{guild.count}\n{guild.icon}\n{guild.id}", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @joindm.command(help="Delete the JoinDM config.")
    async def delete(self, ctx):
        if not ctx.author.guild_permissions.manage_guild:
            embed = discord.Embed(color=0x2f3136, description="⚠️ Missing permission: **Manage Guild**")
            return await ctx.reply(embed=embed, mention_author=False)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM joindm WHERE guild_id = ?", (ctx.guild.id,))
            await db.commit()

        embed = discord.Embed(description="✅ Deleted JoinDM config.", color=0x2f3136)
        await ctx.reply(embed=embed, mention_author=False)

    @joindm.command(help="Send the JoinDM message to yourself as a test.")
    async def test(self, ctx):
        if not ctx.author.guild_permissions.manage_guild:
            embed = discord.Embed(color=0x2f3136, description="⚠️ Missing permission: **Manage Guild**")
            return await ctx.reply(embed=embed, mention_author=False)

        msg = await self.get_message(ctx.guild.id)
        if not msg:
            embed = discord.Embed(description="⚠️ No JoinDM message configured.", color=0x2f3136)
            return await ctx.reply(embed=embed, mention_author=False)

        member = ctx.author
        z = msg.replace('{user}', f'{member}')\
                .replace('{user.name}', f'{member.name}')\
                .replace('{user.mention}', f'{member.mention}')\
                .replace('{user.avatar}', member.avatar.url if member.avatar else '')\
                .replace('{user.joined_at}', f'<t:{int(member.created_at.timestamp())}:R>')\
                .replace('{user.discriminator}', f'{member.discriminator}')\
                .replace('{guild.name}', f'{ctx.guild.name}')\
                .replace('{guild.count}', f'{ctx.guild.member_count}')\
                .replace('{guild.icon}', ctx.guild.icon.url if ctx.guild.icon else '')\
                .replace('{guild.id}', f'{ctx.guild.id}')

        x = await to_object(z)
        try:
            channel = member.dm_channel or await member.create_dm()
            time.sleep(3)
            await channel.send(**x)
            embed = discord.Embed(description="✅ Test message sent to your DMs.", color=0x2f3136)
            await ctx.reply(embed=embed, mention_author=False)
        except:
            await ctx.reply("❌ Couldn't send DM.", mention_author=False)

async def setup(bot):
    await bot.add_cog(JoinDM(bot))
