import discord
from discord.ext import commands

class Dungeon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dungeon_state = {}

    def embed(self, title, desc, color=discord.Color.blurple()):
        return discord.Embed(title=title, description=desc, color=color)

    @commands.command(name="dungeon")
    async def dungeon(self, ctx, action: str = None, *, detail: str = None):
        user_id = ctx.author.id
        action = action.lower() if action else None
        detail = detail.lower() if detail else None

        if not action:
            return await ctx.send(embed=self.embed(
                "🎲 Dungeon Master Lite",
                "Use:\n"
                "• `?dungeon start`\n"
                "• `?dungeon go left/right`\n"
                "• `?dungeon fight`\n"
                "• `?dungeon run`\n"
                "• `?dungeon exit`"
            ))

        if action == "start":
            if user_id in self.dungeon_state:
                return await ctx.send(embed=self.embed("Already Playing", "⚔️ You already started! Try `?dungeon go left`."))
            self.dungeon_state[user_id] = {"stage": "start"}
            return await ctx.send(embed=self.embed(
                "🧭 Crossroads",
                "You stand at a crossroads:\n\n🌲 Left → A dark forest\n⛰️ Right → A steep mountain pass\n\nUse `?dungeon go left` or `?dungeon go right`."
            ))

        elif action == "go":
            if user_id not in self.dungeon_state:
                return await ctx.send(embed=self.embed("Not Playing", "❌ Use `?dungeon start` to begin."))

            if detail == "left":
                self.dungeon_state[user_id]["stage"] = "wolf"
                return await ctx.send(embed=self.embed(
                    "🐺 A Wild Wolf Appears!",
                    "A snarling wolf jumps out from the forest!\nWhat will you do?\n\n• `?dungeon fight`\n• `?dungeon run`"
                ))

            elif detail == "right":
                self.dungeon_state[user_id]["stage"] = "goblin"
                return await ctx.send(embed=self.embed(
                    "👹 Goblin Encounter!",
                    "A goblin blocks your path with a spear!\nYour move:\n\n• `?dungeon fight`\n• `?dungeon run`"
                ))
            else:
                return await ctx.send(embed=self.embed("Invalid Direction", "Please choose `left` or `right`."))

        elif action == "fight":
            if user_id not in self.dungeon_state:
                return await ctx.send(embed=self.embed("Not Playing", "❌ Start with `?dungeon start`."))

            stage = self.dungeon_state[user_id]["stage"]
            if stage in ["wolf", "goblin"]:
                del self.dungeon_state[user_id]
                return await ctx.send(embed=self.embed("⚔️ Victory!", f"You bravely defeated the {stage} and move on."))
            else:
                return await ctx.send(embed=self.embed("❌ No Enemy", "There's nothing to fight right now."))

        elif action == "run":
            if user_id not in self.dungeon_state:
                return await ctx.send(embed=self.embed("Not Playing", "❌ Start with `?dungeon start`."))

            stage = self.dungeon_state[user_id]["stage"]
            if stage in ["wolf", "goblin"]:
                del self.dungeon_state[user_id]
                return await ctx.send(embed=self.embed("🏃 You Escaped!", f"You ran away from the {stage}."))
            else:
                return await ctx.send(embed=self.embed("❌ Can't Run", "There's nothing to run from."))

        elif action == "exit":
            if user_id in self.dungeon_state:
                del self.dungeon_state[user_id]
                return await ctx.send(embed=self.embed("🚪 Dungeon Exited", "Your journey has ended."))
            else:
                return await ctx.send(embed=self.embed("Not Playing", "You're not in a dungeon."))

        else:
            return await ctx.send(embed=self.embed("Unknown Command", "Use `?dungeon` to see all options."))

async def setup(bot):
    await bot.add_cog(Dungeon(bot))