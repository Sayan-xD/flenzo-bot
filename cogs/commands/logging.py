import discord
from discord.ext import commands
from discord.ui import Select, View
import json
import os

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_logging_data()

    def load_logging_data(self):
        if os.path.exists("logging.json"):
            with open("logging.json", "r") as file:
                self.logging_data = json.load(file)
        else:
            self.logging_data = {}

    def save_logging_data(self):
        with open("logging.json", "w") as file:
            json.dump(self.logging_data, file, indent=4)

    @commands.group(
        name="logging",
        invoke_without_command=True,
        description="Shows the logging's help menu"
    )
    async def logging(self, ctx): 
        embed = discord.Embed(
            title="Logging [3]",
            description="< > Duty | [ ] Optional",
            color=0x2f3136
        )
        embed.add_field(name=f"`Logging Setup`", value="Setup logging features.", inline=False)
        embed.add_field(name=f"`Logging Reset`", value="Resets all Logging Config.", inline=False)
        embed.add_field(name=f"`Logging Status`", value="Show Logging Status of this Guild", inline=False)
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.reply(embed=embed)
        embed.set_footer(text=f"Requested By {ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.set_author(name="Flenzo Logging!", icon_url=self.bot.user.display_avatar.url)

    @logging.command(name="setup", description="Setup logging features")
    @commands.has_permissions(administrator=True)
    async def setup_logging(self, ctx):
        view = LoggingSetupView(self.bot)
        embed = discord.Embed(
            title="Logging Setup",
            description="Select the logging feature you want to enable:",
            color=0x2f3136
        )
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        await ctx.reply(embed=embed, view=view)

    async def log_event(self, guild_id, feature, embed):
        if guild_id in self.logging_data:
            if feature in self.logging_data[guild_id]:
                log_channel_id = self.logging_data[guild_id][feature]
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    await log_channel.send(embed=embed)
            if "All Logs" in self.logging_data[guild_id]:
                log_channel_id = self.logging_data[guild_id]["All Logs"]
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    await log_channel.send(embed=embed)

    @logging.command(name="reset", description="Reset the Logging Config")
    @commands.has_permissions(administrator=True)
    async def reset_logging(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.logging_data:
            del self.logging_data[guild_id]
            self.save_logging_data()
            embed = discord.Embed(
                title="Logging Reset",
                description="All logging configurations have been erased for this guild.",
                color=0x2f3136)
        else:
            embed = discord.Embed(
                title="Logging Reset",
                description="No logging configurations found for this guild.",
                color=0x2f3136
            )
            embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)
        
    @logging.command(name="status", description="Shows the Logging Config of this Server")
    @commands.has_permissions(administrator=True)
    async def status(self, ctx):
        guild_id = str(ctx.guild.id)
        embed = discord.Embed(title="Logging Status",
            description=f"Current Logging Status for **{ctx.guild}**",
            color=0x2f3136
        )
        features = [
            "Message Logs", "Member Join/Leave", "Channel Changes", "Role Changes", 
            "Voice State", "Emoji Changes", "Moderation Actions", "All Logs"
        ]
        for feature in features:
            status_text = "Enabled" if guild_id in self.logging_data and feature in self.logging_data[guild_id] else "Disable"
            status_emoji = "<:AnEnable:1317750872326930502>" if guild_id in self.logging_data and feature in self.logging_data[guild_id] else "<:disabled:1317434389621375056>"
            embed.add_field(name=f"{feature} {status_emoji}", value=f"{feature} is Currently **{status_text}** in {ctx.guild}.", inline=False)
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_author(name=f"Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        await ctx.reply(embed=embed)

    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        guild_id = str(after.guild.id)
        embed = discord.Embed(title="Message Edited",
            description=f"> **User:** {after.author.mention}\n> **Channel:** {after.channel.mention}\n> **Before:** {before.content}\n> **After:** {after.content}",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        await self.log_event(guild_id, "Message Logs", embed)

    

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        guild_id = str(message.guild.id)
        embed = discord.Embed(
            title="Message Deleted",
            description=f"> **User:** {message.author.mention}\n> **Channel:** {message.channel.mention}\n> **Content:** {message.content}",
            color=discord.Color.red()
        )
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        await self.log_event(guild_id, "Message Logs", embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        embed = discord.Embed(
            title="Member Joined",
            description=(
                f"> **User:** {member.mention}\n"
                f"> **ID:** {member.id}\n"
                f"> **Account Created At:** {member.created_at}"
            ),
            color=discord.Color.green()
        )
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        await self.log_event(guild_id, "Member Join/Leave", embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = str(member.guild.id)
        embed = discord.Embed(
            title="Member Left",
            description=f"> **User:** {member.mention}\n> **ID:** {member.id}",
            color=discord.Color.red()
        )
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        await self.log_event(guild_id, "Member Join/Leave", embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild_id = str(channel.guild.id)
        embed = discord.Embed(
            title="Channel Created",
            description=(
                f"> **Channel:** {channel.mention}\n"
                f"> **ID:** {channel.id}\n"
                f"> **Category:** {channel.category}\n"
                f"> **Position:** {channel.position}"
            ),
            color=discord.Color.green()
        )
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        await self.log_event(guild_id, "Channel Changes", embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild_id = str(channel.guild.id)
        embed = discord.Embed(
            title="Channel Deleted",
            description=f"> **Channel:** {channel.name}\n**> ID:** {channel.id}",
            color=discord.Color.red()
        )
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        embed.set_thumbnail(url=channel.guild.icon.url)
        await self.log_event(guild_id, "Channel Changes", embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild_id = str(role.guild.id)
        embed = discord.Embed(
            title="Role Created",
            description=(
                f"> **Role:** {role.name}\n"
                f"> **ID:** {role.id}\n"
                f"**Color:** {role.color}\n"
                f"> **Permissions:** {role.permissions}\n"
                f"> **Mentionable:** {role.mentionable}\n"
                f"> **Created At:** {role.created_at}"
            ),
            color=discord.Color.green())
        embed.set_thumbnail(url=role.icon.url if role.icon else role.guild.icon.url)
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        
        await self.log_event(guild_id, "Role Changes", embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild_id = str(role.guild.id)
        embed = discord.Embed(
            title="Role Deleted",
            description=f"> **Role:** {role.name}\n> **ID:** {role.id}\n",
            color=discord.Color.red()
        )
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        await self.log_event(guild_id, "Role Changes", embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild_id = str(member.guild.id)
        embed = discord.Embed(
            title="Voice State Update",
            description=f"> **User:** {member.mention}\n**> Before:** {before.channel}\n**> After:** {after.channel}",
            color=discord.Color.blue()
        )
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        await self.log_event(guild_id, "Voice State", embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        guild_id = str(guild.id)
        embed = discord.Embed(
            title="Emoji Updated",
            description=f"> **Before:** {before}\n> **After:** {after}",
            color=discord.Color.blue()
        )
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        await self.log_event(guild_id, "Emoji Changes", embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        guild_id = str(guild.id)
        embed = discord.Embed(
            title="Member Banned",
            description=f"> **User:** {user.mention}\n> **ID:** {user.id}",
            color=discord.Color.red()
        )
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        await self.log_event(guild_id, "Moderation Actions", embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        guild_id = str(guild.id)
        embed = discord.Embed(
            title="Member Unbanned",
            description=f"> **User:** {user.mention}\n> **ID:** {user.id}",
            color=discord.Color.green()
        )
        embed.set_author(name="Flenzo Logging System!", icon_url=self.bot.user.display_avatar.url)
        await self.log_event(guild_id, "Moderation Actions", embed)

class LoggingSetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot
        self.add_item(LoggingSelect(bot))

class LoggingSelect(Select):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x2f3136
        self.greencolor = 0x00FF00
        options = [
            discord.SelectOption(label="Message Logs", description="Log deleted/edited messages."),
            discord.SelectOption(label="Member Join/Leave", description="Log member join/leave events."),
            discord.SelectOption(label="Channel Changes", description="Log channel changes."),
            discord.SelectOption(label="Role Changes", description="Log role changes."),
            discord.SelectOption(label="Voice State", description="Log voice state updates."),
            discord.SelectOption(label="Emoji Changes", description="Log emoji changes."),
            discord.SelectOption(label="Moderation Actions", description="Log moderation actions."),
            discord.SelectOption(label="All Logs", description="Log all types of events.")
        ]
        super().__init__(placeholder="Choose a logging feature...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        feature = self.values[0]
        await self.setup_logging_feature(interaction, feature)

    async def setup_logging_feature(self, interaction: discord.Interaction, feature: str):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.bot.cogs['Logging'].logging_data:
            self.bot.cogs['Logging'].logging_data[guild_id] = {}

        if feature in self.bot.cogs['Logging'].logging_data[guild_id]:
            await interaction.response.send_message(embed=discord.Embed(title="Error Found", description=f"**{feature}** is already Enabled for this Server.", color=discord.Color.red()), ephemeral=True)
        else:
            await interaction.response.send_message(embed=discord.Embed(title="**Channel** Selection", description=f"Please mention the channel or provide the channel ID for **{feature}**.", color=self.color), ephemeral=True)
            

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                channel_id = int(msg.content.strip('<>#'))
                channel = interaction.guild.get_channel(channel_id)
                if channel:
                    self.bot.cogs['Logging'].logging_data[guild_id][feature] = channel.id
                    self.bot.cogs['Logging'].save_logging_data()
                    await interaction.followup.send(embed=discord.Embed(description=f"<:IconTick:1381245157759782975> | Successfully Enabled **{feature}**. and Logs will be Sent to {channel.mention}.", color=self.greencolor), ephemeral=True)
                else:
                    raise ValueError("Invalid channel")
            except:
                await interaction.followup.send(embed=discord.Embed(title="Error", description="Invalid channel. Please try the setup Command again.", color=discord.Color.red()), ephemeral=True)


async def setup(bot):
    await bot.add_cog(Logging(bot))


