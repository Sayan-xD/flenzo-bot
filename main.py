import os
import asyncio
import traceback
from threading import Thread
from datetime import datetime

import aiohttp
import discord
from discord.ext import commands
import wavelink

from core import Context
from core.Cog import Cog
from core.Flenzo import Flenzo
from utils.Tools import *
from utils.config import *

import jishaku
import cogs

# ────────────────────────────── Jishaku Config ──────────────────────────────
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "False"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"

# ────────────────────────────── Bot Initialization ──────────────────────────────
client = Flenzo()
tree = client.tree
TOKEN = os.getenv("TOKEN")  # Replace with your real token

# ──────────────── Lavalink Node Config (Danbot) ────────────────
WAVELINK_NODE = {
    "uri": "http://104.167.222.158:5093",
    "password": "sayanop"
}

# ────────────────────────────── Full Command Utility ──────────────────────────────
def get_full_command(ctx):
    if hasattr(ctx, "message") and ctx.message:
        return ctx.message.content
    elif hasattr(ctx, "interaction") and ctx.interaction:
        data = ctx.interaction.data
        base = f"/{data['name']}"
        options = data.get("options", [])
        if options:
            args = " ".join(f"{opt['name']}: {opt['value']}" for opt in options)
            return f"{base} {args}"
        else:
            return base
    return "Unknown command"

# ────────────────────────────── Bot Ready Event ──────────────────────────────
@client.event
async def on_ready():
    await client.wait_until_ready()

    try:
        node = wavelink.Node(
            uri=WAVELINK_NODE["uri"],
            password=WAVELINK_NODE["password"]
        )
        await wavelink.Pool.connect(nodes=[node], client=client)
        print("✅ Lavalink node connected!")
    except Exception as e:
        print("❌ Lavalink connection failed:", e)

    print("""
           \033[1;93m
███████╗██╗░░░░░███████╗███╗░░██╗███████╗░█████╗░
██╔════╝██║░░░░░██╔════╝████╗░██║╚════██║██╔══██╗
█████╗░░██║░░░░░█████╗░░██╔██╗██║░░███╔═╝██║░░██║
██╔══╝░░██║░░░░░██╔══╝░░██║╚████║██╔══╝░░██║░░██║
██║░░░░░███████╗███████╗██║░╚███║███████╗╚█████╔╝
╚═╝░░░░░╚══════╝╚══════╝╚═╝░░╚══╝╚══════╝░╚════╝░
       \033[1;93m
           """)
    print("Loaded & Online!")
    print(f"Logged in as: {client.user}")
    print(f"Connected to: {len(client.guilds)} guilds")
    print(f"Connected to: {len(client.users)} users")
    try:
        synced = await client.tree.sync()
        all_commands = list(client.commands)
        print(f"Synced Total {len(all_commands)} Client Commands and {len(synced)} Slash Commands")
    except Exception as e:
        print(e)

# ────────────────────────────── Command Logging ──────────────────────────────
@client.event
async def on_command_completion(context: commands.Context) -> None:
    if context.author.id == 961805595449638952:
        return

    full_command = get_full_command(context)
    executed_command = context.command.qualified_name
    webhook_url = "https://discord.com/api/webhooks/1390140740239229109/PDn1_1qKvsUtjTxLFxSFOY3BVd1-lE3ukTUSr6RLe_9FJQPExrTM1Shdc8o2JEufCaDR"  # Optional logging webhook

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(webhook_url, session=session)
        avatar_url = context.author.display_avatar.url

        try:
            embed = discord.Embed(color=0x000000)
            embed.set_author(
                name=f"Executed {executed_command} Command By : {context.author}",
                icon_url=avatar_url
            )
            embed.set_thumbnail(url=avatar_url)

            embed.add_field(name="📝 Full Command :", value=f"{full_command}", inline=False)
            embed.add_field(name="🙋‍♂️ Command Executed By :", value=f"{context.author}", inline=False)

            if context.guild:
                embed.add_field(name="🌐 Guild :", value=f"{context.guild.name} (ID: {context.guild.id})", inline=False)
                embed.add_field(name="📄 Channel :", value=f"{context.channel.name} | ID: [{context.channel.id}](https://discord.com/channels/{context.guild.id}/{context.channel.id})", inline=False)

            embed.timestamp = discord.utils.utcnow()
            embed.set_footer(text="SayaN On Top", icon_url=client.user.display_avatar.url)

            await webhook.send(embed=embed)
        except Exception as e:
            print(f'Command logging failed: {e}')
            traceback.print_exc()

# ────────────────────────────── Uptime Server ──────────────────────────────
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "© Revolution X Est.2021"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

keep_alive()

# ────────────────────────────── Main Entrypoint ──────────────────────────────
async def main():
    async with client:
        os.system("clear")
        await client.load_extension("jishaku")
        await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
