
from __future__ import annotations
from core import Flenzo
from colorama import Fore, Style, init


#----------Commands---------#
from .commands.help import Help
from .commands.Ping import Ping
from .commands.aly import VC247
from .commands.dungeon import Dungeon
from .commands.emergency import Emergency
from .commands.Nop import NoPrefixClaim, ClaimView
from .commands.track import Track
from .commands.premium import Premium, is_premium
from .commands.fastgreet import FastGreet
from .commands.invites import InviteTracker
from .commands.boycott import Boycott
from .commands.reactionrole import ReactionRoles
from .commands.badges import Badges
from .commands.birthday import Birthday
from .commands.sin import OwnerCommands
from .commands.joindm import JoinDM
from .commands.votereact import VoteReact
from .commands.vanityroles import Vanityroles
from .commands.general import General
from .commands.music import Music
from .commands.welcome import Welcomer
from .commands.sticky import StickyMessage
from .commands.ticket import ticket, ticketpanel, ticketchannelpanel, tickredel
from .commands.fun import Fun
from .commands.fun1 import Fun1
from .commands.extra import Extra
from .commands.owner import Owner
from .commands.voice import Voice
from .commands.afk import afk
from .commands.ignore import Ignore
from .commands.Invc import Invcrole
from .commands.giveaway import Giveaway
from .commands.Embed import Embed
from .commands.steal import Steal
from .commands.timer import Timer
from .commands.block import Block
from .commands.nightmode import Nightmode
from .commands.imagine import AiStuffCog
from .commands.map import Map
from .commands.logging import Logging
from .commands.autoresponder import AutoResponder
from .commands.customrole import Customrole
from .commands.autorole import AutoRole
from .commands.extraown import Extraowner
from .commands.anti_wl import Whitelist
from .commands.anti_unwl import Unwhitelist
from .commands.slots import Slots
from .commands.blackjack import Blackjack
from .commands.autoreact import AutoReaction
from .commands.stats import Stats
from .commands.notify import NotifCommands
from .commands.status import Status
from .commands.np import NoPrefix
from .commands.filters import FilterCog
from .commands.owner2 import Global
from .commands.vote import Vote
from .commands.fp import ForcePrefix
# from .commands.activity import Activity

#____________ Events _____________
from .events.Errors import Errors
from .events.on_guild import Guild
from .events.autorole import Autorole2
from .events.auto import Autorole
from .events.greet2 import greet
from .events.mention import Mention
from .events.react import React
from .events.autoreact import AutoReactListener
from .events.topgg import TopGG

########-------HELP-------########
from .flenzo.security import sayan1
from .flenzo.extra import sayan11
from .flenzo.general import sayan111
from .flenzo.automod import sayan11111
from .flenzo.moderation import sayan111111
from .flenzo.music import sayanMusic
from .flenzo.fun import sayan111111111
from .flenzo.games import sayan1111111111
from .flenzo.ticket import sayanticket
from .flenzo.ignore import sayanIgnore
from .flenzo.server import sayan11111111111
from .flenzo.voice import sayan1111111111111
from .flenzo.welcome import sayan11111111111111
from .flenzo.logging import Loggingdrop
from .flenzo.media import sayanMedia
from .flenzo.vcroles import vcrole66
from .flenzo.giveaway import sayan11111111111111111
from .flenzo.vanityroles import Vanityroles69999
from .flenzo.sticky import _stickymessage
from .flenzo.track import sayanTrack
from .flenzo.fastgreet import fastgreet


#########ANTINUKE#########
from .events.anti_member_update import AntiMemberUpdate
from .events.antiban import AntiBan
from .events.antibotadd import AntiBotAdd
from .events.antichcr import AntiChannelCreate
from .events.antichdl import AntiChannelDelete
from .events.antichup import AntiChannelUpdate
from .events.antieveryone import AntiEveryone
from .events.antiguild import AntiGuildUpdate
from .events.antiIntegration import AntiIntegration
from .events.antikick import AntiKick
from .events.antiprune import AntiPrune
from .events.antirlcr import AntiRoleCreate
from .events.antirldl import AntiRoleDelete
from .events.antirlup import AntiRoleUpdate
from .events.antiwebhook import AntiWebhookUpdate
from .events.antiwebhookcr import AntiWebhookCreate
from .events.antiwebhookdl import AntiWebhookDelete

# Extra Optional Events
# from .events.antinuke.antiemocr import AntiEmojiCreate
# from .events.antinuke.antiemodl import AntiEmojiDelete
# from .events.antinuke.antiemoup import AntiEmojiUpdate
# from .events.antinuke.antisticker import AntiSticker


############ AUTOMOD ############
from .events.antispam import AntiSpam
from .events.anticaps import AntiCaps
from .events.antilink import AntiLink
from .events.anti_invites import AntiInvite
from .events.anti_mass_mention import AntiMassMention
from .events.anti_emoji_spam import AntiEmojiSpam


from .moderation.ban import Ban
from .moderation.unban import Unban
from .moderation.timeout import Mute
from .moderation.unmute import Unmute
from .moderation.lock import Lock
from .moderation.unlock import Unlock
from .moderation.hide import Hide
from .moderation.unhide import Unhide
from .moderation.kick import Kick
from .moderation.warn import Warn
from .moderation.role import Role
from .moderation.message import Message
from .moderation.moderation import Moderation
from .moderation.topcheck import TopCheck
from .moderation.snipe import Snipe


async def setup(bot: Flenzo):
    cogs_to_load = [
        Help, General, Moderation, Welcomer, Fun, Extra,
        Voice, Owner, Customrole, afk, Embed, Ignore,
        Invcrole, Steal, Timer,
        Block, Nightmode, AiStuffCog, Whitelist,
        Unwhitelist, Extraowner, Map, Logging, Blackjack, Slots,
        Guild, Errors, Autorole2, Autorole, greet, AutoResponder,
        Mention, AutoRole, React, AntiMemberUpdate, AntiBan, AntiBotAdd,
        AntiChannelCreate, AntiChannelDelete, AntiChannelUpdate, AntiEveryone, AntiGuildUpdate,
        AntiIntegration, AntiKick, AntiPrune, AntiRoleCreate, AntiRoleDelete,
        AntiRoleUpdate, AntiWebhookUpdate, AntiWebhookCreate,
        AntiWebhookDelete, AntiSpam, AntiCaps, AntiLink, AntiInvite, AntiMassMention, Music, Stats, Status, NoPrefix, FilterCog, AutoReaction, AutoReactListener, Ban, Unban, Mute, Unmute, Lock, Unlock, Hide, Unhide, Kick, Warn, Role, Message, Moderation, TopCheck, Snipe, Global, InviteTracker, Fun1, OwnerCommands, VoteReact, Birthday, StickyMessage, Premium, NoPrefixClaim, Vanityroles, Badges, Track, Dungeon, ticket, ReactionRoles, FastGreet, Ping, ForcePrefix, VC247, Boycott, Emergency
    ]

    await bot.add_cog(Help(bot))
    await bot.add_cog(General(bot))
    await bot.add_cog(Music(bot))
    await bot.add_cog(Welcomer(bot))
    await bot.add_cog(Fun(bot))
    await bot.add_cog(Extra(bot))
    await bot.add_cog(Voice(bot))
    await bot.add_cog(Owner(bot))
    await bot.add_cog(Customrole(bot))
    await bot.add_cog(afk(bot))
    await bot.add_cog(Logging(bot))
    await bot.add_cog(Embed(bot))
    await bot.add_cog(Ignore(bot))
    await bot.add_cog(Invcrole(bot))
    await bot.add_cog(Giveaway(bot))
    await bot.add_cog(Steal(bot))
    await bot.add_cog(Timer(bot))
    await bot.add_cog(Block(bot))
    await bot.add_cog(Nightmode(bot))
    await bot.add_cog(AiStuffCog(bot))
    await bot.add_cog(Whitelist(bot))
    await bot.add_cog(Unwhitelist(bot))
    await bot.add_cog(Extraowner(bot))
    await bot.add_cog(Slots(bot))
    await bot.add_cog(Blackjack(bot))
    await bot.add_cog(Stats(bot))
    await bot.add_cog(Status(bot))
    await bot.add_cog(NoPrefix(bot))
    await bot.add_cog(FilterCog(bot))
    await bot.add_cog(Global(bot))
    await bot.add_cog(InviteTracker(bot))
    await bot.add_cog(Fun1(bot))
    await bot.add_cog(JoinDM(bot))
    await bot.add_cog(Vote(bot))
    await bot.add_cog(OwnerCommands(bot))
    await bot.add_cog(VoteReact(bot))
    await bot.add_cog(Birthday(bot))
    await bot.add_cog(StickyMessage(bot))
    await bot.add_cog(Premium(bot))
    await bot.add_cog(NoPrefixClaim(bot))
    await bot.add_cog(Vanityroles(bot))
    await bot.add_cog(Badges(bot))
    await bot.add_cog(Track(bot))
    await bot.add_cog(Dungeon(bot))
    await bot.add_cog(ticket(bot))
    await bot.add_cog(ReactionRoles(bot))
    await bot.add_cog(FastGreet(bot))
    await bot.add_cog(Ping(bot))
    await bot.add_cog(ForcePrefix(bot))
    await bot.add_cog(VC247(bot))
    await bot.add_cog(Boycott(bot))
    await bot.add_cog(Emergency(bot))

    # ✅ Insert yeh yahan 👇
    bot.add_view(ticketpanel(bot))
    bot.add_view(ticketchannelpanel(bot))
    bot.add_view(tickredel(bot))
    bot.add_view(ClaimView())
    # await bot.add_cog(Activity(bot))

    await bot.add_cog(sayan1(bot))
    await bot.add_cog(sayan11111(bot))
    await bot.add_cog(sayan11111111111(bot))
    await bot.add_cog(sayan11(bot))
    await bot.add_cog(sayan111(bot))
    await bot.add_cog(sayan111111(bot))
    await bot.add_cog(sayanMusic(bot))
    await bot.add_cog(sayan11111111111111111(bot))
    await bot.add_cog(sayan111111111(bot))
    await bot.add_cog(sayanticket(bot))
    await bot.add_cog(sayanIgnore(bot))
    await bot.add_cog(sayanMedia(bot))
    await bot.add_cog(sayan1111111111(bot))
    await bot.add_cog(sayan1111111111111(bot))
    await bot.add_cog(sayan11111111111111(bot))
    await bot.add_cog(Vanityroles69999(bot))
    await bot.add_cog(vcrole66(bot))
    await bot.add_cog(Loggingdrop(bot))
    await bot.add_cog(Map(bot))
    await bot.add_cog(sayanTrack(bot))
    await bot.add_cog(fastgreet(bot))

    ###########################events################
    await bot.add_cog(Guild(bot))
    await bot.add_cog(TopGG(bot))
    await bot.add_cog(Errors(bot))
    await bot.add_cog(Autorole2(bot))
    await bot.add_cog(Autorole(bot))
    await bot.add_cog(greet(bot))
    await bot.add_cog(AutoResponder(bot))
    await bot.add_cog(Mention(bot))
    await bot.add_cog(AutoRole(bot))
    await bot.add_cog(React(bot))
    await bot.add_cog(AutoReaction(bot))
    await bot.add_cog(AutoReactListener(bot))
    await bot.add_cog(NotifCommands(bot))

    await bot.add_cog(AntiMemberUpdate(bot))
    await bot.add_cog(AntiBan(bot))
    await bot.add_cog(AntiBotAdd(bot))
    await bot.add_cog(AntiChannelCreate(bot))
    await bot.add_cog(AntiChannelDelete(bot))
    await bot.add_cog(AntiChannelUpdate(bot))
    await bot.add_cog(AntiEveryone(bot))
    await bot.add_cog(AntiGuildUpdate(bot))
    await bot.add_cog(AntiIntegration(bot))
    await bot.add_cog(AntiKick(bot))
    await bot.add_cog(AntiPrune(bot))
    await bot.add_cog(AntiRoleCreate(bot))
    await bot.add_cog(AntiRoleDelete(bot))
    await bot.add_cog(AntiRoleUpdate(bot))
    await bot.add_cog(AntiWebhookUpdate(bot))
    await bot.add_cog(AntiWebhookCreate(bot))
    await bot.add_cog(AntiWebhookDelete(bot))

    await bot.add_cog(AntiSpam(bot))
    await bot.add_cog(AntiCaps(bot))
    await bot.add_cog(AntiInvite(bot))
    await bot.add_cog(AntiLink(bot))
    await bot.add_cog(AntiMassMention(bot))
    await bot.add_cog(AntiEmojiSpam(bot))

    await bot.add_cog(Ban(bot))
    await bot.add_cog(Unban(bot))
    await bot.add_cog(Mute(bot))
    await bot.add_cog(Unmute(bot))
    await bot.add_cog(Lock(bot))
    await bot.add_cog(Unlock(bot))
    await bot.add_cog(Hide(bot))
    await bot.add_cog(Unhide(bot))
    await bot.add_cog(Kick(bot))
    await bot.add_cog(Warn(bot))
    await bot.add_cog(Role(bot))
    await bot.add_cog(Message(bot))
    await bot.add_cog(Moderation(bot))
    await bot.add_cog(TopCheck(bot))
    await bot.add_cog(Snipe(bot))

    for cog in cogs_to_load:
        print(Fore.RED + Style.BRIGHT + f"Loaded cog: {cog.__name__}")
    print(Fore.BLUE + Style.BRIGHT + "All cogs loaded successfully.")
