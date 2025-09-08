# File: cogs/commands/birthday.py
import os,datetime,asyncio,pytz,logging
from typing import Optional,List
from dataclasses import dataclass
import discord
from discord.ext import commands,tasks
import aiosqlite
from core.Flenzo import Flenzo
from utils.Tools import blacklist_check

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)
logger.disabled = True

DB_PATH,MONTHS="db/birthdays.db",["January","February","March","April","May","June","July","August","September","October","November","December"]
DAYS=[31,29,31,30,31,30,31,31,30,31,30,31]
IST=pytz.timezone('Asia/Kolkata')

def ist_now():return datetime.datetime.now(IST)
def ist_today():return ist_now().date()
def ord(n):return f"{n}{'th' if 10<=n%100<=20 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th')}"
def valid_date(d,m,y=None):return 1<=m<=12 and 1<=d<=DAYS[m-1] and (not y or y>=1900) and (m!=2 or d!=29 or not y or y%4==0 and(y%100!=0 or y%400==0))

class BirthdayError(Exception):pass

@dataclass
class BD:
    user_id:int;day:int;month:int;year:Optional[int]=None
    @property
    def age(self):
        if self.year:
            t=ist_today();a=t.year-self.year
            return a-1 if(t.month,t.day)<(self.month,self.day)else a
    @property
    def next_bd(self):
        t=ist_today()
        try:n=datetime.date(t.year,self.month,self.day);return n if n>=t else datetime.date(t.year+1,self.month,self.day)
        except:return datetime.date(t.year+1,2,28)if self.month==2 and self.day==29 else None

@dataclass
class GS:
    guild_id:int;role_id:Optional[int]=None;auto_remove:bool=True;channel_id:Optional[int]=None
    message_template:str="<a:tadaa:1391669106754981958> Happy Birthday {mention}! <a:animated_cake:1391668759152037898>"

class BDB:
    def __init__(self,p=DB_PATH):self.p,self.i=p,False
    
    async def init(self):
        try:
            os.makedirs(os.path.dirname(self.p),exist_ok=True)
            async with aiosqlite.connect(self.p)as db:
                await db.executescript("""CREATE TABLE IF NOT EXISTS birthdays(guild_id INTEGER NOT NULL,user_id INTEGER NOT NULL,day INTEGER NOT NULL,month INTEGER NOT NULL,year INTEGER,created_at INTEGER DEFAULT(strftime('%s','now')),PRIMARY KEY(guild_id,user_id));CREATE TABLE IF NOT EXISTS birthday_settings(guild_id INTEGER PRIMARY KEY,role_id INTEGER,auto_remove INTEGER DEFAULT 1,channel_id INTEGER,message_template TEXT DEFAULT '<a:tadaa:1391669106754981958> Happy Birthday {mention}! <a:animated_cake:1391668759152037898>');CREATE INDEX IF NOT EXISTS idx_birthdays_date ON birthdays(month,day);""")
                await db.commit()
            self.i=True;logger.info("DB init success")
        except Exception as e:logger.error(f"DB init failed: {e}");raise BirthdayError(f"DB init failed: {e}")
    
    async def _ei(self):
        if not self.i:await self.init()
    
    async def set_bd(self,g,u,d,m,y=None):
        await self._ei()
        if not valid_date(d,m,y):raise BirthdayError("Invalid date")
        try:
            async with aiosqlite.connect(self.p)as db:
                await db.execute("INSERT INTO birthdays(guild_id,user_id,day,month,year)VALUES(?,?,?,?,?)ON CONFLICT(guild_id,user_id)DO UPDATE SET day=excluded.day,month=excluded.month,year=excluded.year",(g,u,d,m,y))
                await db.commit()
            logger.info(f"Set BD {u} in {g}: {d}/{m}/{y}");return True
        except Exception as e:logger.error(f"Failed save BD: {e}");raise BirthdayError(f"Failed save BD: {e}")
    
    async def get_bd(self,g,u):
        await self._ei()
        try:
            async with aiosqlite.connect(self.p)as db:
                c=await db.execute("SELECT day,month,year FROM birthdays WHERE guild_id=? AND user_id=?",(g,u))
                r=await c.fetchone()
                return BD(u,r[0],r[1],r[2])if r else None
        except Exception as e:logger.error(f"Failed get BD: {e}");return None
    
    async def del_bd(self,g,u):
        await self._ei()
        try:
            async with aiosqlite.connect(self.p)as db:
                c=await db.execute("DELETE FROM birthdays WHERE guild_id=? AND user_id=?",(g,u))
                await db.commit();return c.rowcount>0
        except Exception as e:logger.error(f"Failed del BD: {e}");return False
    
    async def get_guild_bds(self,g):
        await self._ei()
        try:
            async with aiosqlite.connect(self.p)as db:
                c=await db.execute("SELECT user_id,day,month,year FROM birthdays WHERE guild_id=?",(g,))
                return[BD(r[0],r[1],r[2],r[3])for r in await c.fetchall()]
        except Exception as e:logger.error(f"Failed get guild BDs: {e}");return[]
    
    async def get_today_bds(self,g):
        t=ist_today();await self._ei()
        try:
            async with aiosqlite.connect(self.p)as db:
                c=await db.execute("SELECT user_id,day,month,year FROM birthdays WHERE guild_id=? AND day=? AND month=?",(g,t.day,t.month))
                r=[BD(x[0],x[1],x[2],x[3])for x in await c.fetchall()]
                logger.info(f"Found {len(r)} BDs for today in {g}");return r
        except Exception as e:logger.error(f"Failed get today BDs: {e}");return[]
    
    async def set_gs(self,s):
        await self._ei()
        try:
            async with aiosqlite.connect(self.p)as db:
                await db.execute("INSERT OR REPLACE INTO birthday_settings(guild_id,role_id,auto_remove,channel_id,message_template)VALUES(?,?,?,?,?)",(s.guild_id,s.role_id,s.auto_remove,s.channel_id,s.message_template))
                await db.commit()
            logger.info(f"Updated settings {s.guild_id}");return True
        except Exception as e:logger.error(f"Failed set settings: {e}");return False
    
    async def get_gs(self,g):
        await self._ei()
        try:
            async with aiosqlite.connect(self.p)as db:
                c=await db.execute("SELECT role_id,auto_remove,channel_id,message_template FROM birthday_settings WHERE guild_id=?",(g,))
                r=await c.fetchone()
                return GS(g,r[0],bool(r[1]),r[2],r[3]or"<a:tadaa:1391669106754981958> Happy Birthday {mention}! <a:animated_cake:1391668759152037898>")if r else GS(g)
        except Exception as e:logger.error(f"Failed get settings: {e}");return GS(g)

class Birthday(commands.Cog):
    def __init__(self,bot:Flenzo):
        self.bot,self.db,self._rt=bot,BDB(),{}
        self.bot.loop.create_task(self.db.init())
        self.daily_check.start()
    
    def cog_unload(self):
        self.daily_check.cancel()
        for t in self._rt.values():t.cancel()
    
    def _e(self,t,d,c):
        e=discord.Embed(title=t,description=d,color=c)
        e.set_footer(text=f"Birthday System • {ist_now().strftime('%Y-%m-%d %H:%M IST')}")
        return e
    
    def _fd(self,d,m,y=None):return f"{ord(d)} of {MONTHS[m-1]}{f', {y}'if y else''}"
    
    async def _se(self,ctx,msg):await ctx.send(embed=self._e("<:cross:1389464521659388035> Error",msg,discord.Color.red()))
    async def _ss(self,ctx,msg):await ctx.send(embed=self._e("<:tick:1389464308475363399> Success",msg,discord.Color.green()))
    
    async def _ar(self,m,s):
        if not s.role_id:return
        try:
            r=m.guild.get_role(s.role_id)
            if not r or r in m.roles:return
            await m.add_roles(r,reason="BD role")
            logger.info(f"Assigned BD role to {m.display_name}")
            if s.auto_remove:await self._sr(m,r)
        except Exception as e:logger.error(f"Failed assign role: {e}")
    
    async def _sr(self,m,r):
        k=f"{m.guild.id}_{m.id}"
        if k in self._rt:self._rt[k].cancel()
        self._rt[k]=asyncio.create_task(self._rr(m,r,86400))
    
    async def _rr(self,m,r,d):
        try:
            await asyncio.sleep(d)
            m=m.guild.get_member(m.id)
            if m and r in m.roles:await m.remove_roles(r,reason="BD role auto-remove");logger.info(f"Removed BD role from {m.display_name}")
        except Exception as e:logger.error(f"Role removal failed: {e}")
        finally:
            k=f"{m.guild.id}_{m.id}"
            if k in self._rt:del self._rt[k]
    
    async def _sm(self,g,m,s,bd):
        if not s.channel_id:return
        try:
            c=g.get_channel(s.channel_id)
            if not c:return
            msg=s.message_template.format(mention=m.mention)
            e=discord.Embed(title="<a:tadaa:1391669106754981958> Happy Birthday!",description=msg,color=discord.Color.gold())
            if bd.age:e.add_field(name="Age",value=f"{bd.age} years old",inline=True)
            e.add_field(name="Birthday",value=self._fd(bd.day,bd.month,bd.year),inline=True)
            e.set_thumbnail(url=m.avatar.url if m.avatar else m.default_avatar.url)
            e.set_footer(text=f"Birthday System • {ist_now().strftime('%Y-%m-%d %H:%M IST')}")
            await c.send(embed=e);logger.info(f"Sent BD msg for {m.display_name}")
        except Exception as e:logger.error(f"Failed send BD msg: {e}")
    
    @tasks.loop(hours=24)
    async def daily_check(self):
        try:
            for g in self.bot.guilds:
                bds=await self.db.get_today_bds(g.id)
                if not bds:continue
                s=await self.db.get_gs(g.id)
                for bd in bds:
                    m=g.get_member(bd.user_id)
                    if m:await self._ar(m,s);await self._sm(g,m,s,bd)
        except Exception as e:logger.error(f"Daily check failed: {e}")
    
    @daily_check.before_loop
    async def before_daily_check(self):
        await self.bot.wait_until_ready()
        now=ist_now()
        next_run=now.replace(hour=0,minute=0,second=0,microsecond=0)+datetime.timedelta(days=1)
        await asyncio.sleep((next_run-now).total_seconds())
    
    @commands.group(name="birthday",aliases=["bd"],invoke_without_command=True)
    @blacklist_check()
    async def birthday(self,ctx):await ctx.send_help(ctx.command)
    
    @birthday.command(name="set")
    async def set_bd(self,ctx,day:int,month:int,year:Optional[int]=None):
        try:
            if not valid_date(day,month,year):return await self._se(ctx,"Invalid date! Use: `day month [year]`\nExample: `15 3` or `15 3 1995`")
            if year and year>ist_today().year:return await self._se(ctx,"Birth year cannot be future!")
            if await self.db.set_bd(ctx.guild.id,ctx.author.id,day,month,year):await self._ss(ctx,f"Birthday set to **{self._fd(day,month,year)}**")
            else:await self._se(ctx,"Failed to save birthday.")
        except Exception as e:logger.error(f"Error setting BD: {e}");await self._se(ctx,"Unexpected error occurred.")
    
    @birthday.command(name="check",aliases=["show"])
    async def check_bd(self,ctx,member:Optional[discord.Member]=None):
        t=member or ctx.author
        try:
            bd=await self.db.get_bd(ctx.guild.id,t.id)
            if not bd:return await ctx.send(embed=self._e("<a:animated_cake:1391668759152037898> Birthday",f"{'You have' if t==ctx.author else f'{t.display_name} has'} no birthday set.",discord.Color.orange()))
            d=self._fd(bd.day,bd.month,bd.year)
            desc=f"{t.mention}: **{d}**"
            if bd.age:desc+=f"\n**Age:** {bd.age} years old"
            nb=bd.next_bd;du=(nb-ist_today()).days
            if du==0:desc+="\n<a:tadaa:1391669106754981958> **Today is their birthday!**"
            elif du==1:desc+="\n<:giveaway:1389603154227630193> **Birthday is tomorrow!**"
            else:desc+=f"\n<:Calender:1391669491577917441> **Next birthday in {du} days**"
            await ctx.send(embed=self._e("<a:animated_cake:1391668759152037898> Birthday",desc,discord.Color.blurple()))
        except Exception as e:logger.error(f"Error checking BD: {e}");await self._se(ctx,"Failed to check birthday.")
    
    @birthday.command(name="delete",aliases=["remove"])
    async def del_bd(self,ctx):
        try:
            if await self.db.del_bd(ctx.guild.id,ctx.author.id):await self._ss(ctx,"Birthday removed.")
            else:await self._se(ctx,"No birthday set.")
        except Exception as e:logger.error(f"Error deleting BD: {e}");await self._se(ctx,"Failed to delete birthday.")
    
    @birthday.command(name="list",aliases=["board"])
    async def list_bds(self,ctx):
        try:
            bds=await self.db.get_guild_bds(ctx.guild.id)
            if not bds:return await ctx.send(embed=self._e("<:support:1389602575849881600> Birthday List","No birthdays set.",discord.Color.orange()))
            bds.sort(key=lambda x:x.next_bd);ls=[]
            for i,bd in enumerate(bds[:20],1):
                m=ctx.guild.get_member(bd.user_id)
                if m:
                    ds=self._fd(bd.day,bd.month);du=(bd.next_bd-ist_today()).days
                    st="<a:tadaa:1391669106754981958> Today!" if du==0 else "<:giveaway:1389603154227630193> Tomorrow" if du==1 else f"<:Calender:1391669491577917441> {du} days"
                    ls.append(f"{i}. {m.mention} — {ds} ({st})")
            if len(bds)>20:ls.append("... and more")
            await ctx.send(embed=self._e("<a:animated_cake:1391668759152037898> Birthday List","\n".join(ls),discord.Color.gold()))
        except Exception as e:logger.error(f"Error listing BDs: {e}");await self._se(ctx,"Failed to list birthdays.")
    
    @birthday.command(name="today")
    async def today_bds(self,ctx):
        try:
            bds=await self.db.get_today_bds(ctx.guild.id)
            if not bds:return await ctx.send(embed=self._e("<a:animated_cake:1391668759152037898> Today's Birthdays","No birthdays today!",discord.Color.orange()))
            ls=[]
            for bd in bds:
                m=ctx.guild.get_member(bd.user_id)
                if m:ls.append(f"<a:tadaa:1391669106754981958> {m.mention}{f' (turning {bd.age})'if bd.age else''}")
            await ctx.send(embed=self._e("<a:tadaa:1391669106754981958> Today's Birthdays","\n".join(ls),discord.Color.green()))
        except Exception as e:logger.error(f"Error getting today BDs: {e}");await self._se(ctx,"Failed to get today's birthdays.")
    
    @birthday.command(name="next",aliases=["upcoming"])
    async def next_bds(self,ctx,count:int=5):
        count=min(count,20)
        try:
            bds=await self.db.get_guild_bds(ctx.guild.id)
            if not bds:return await ctx.send(embed=self._e("<:Calender:1391669491577917441> Upcoming Birthdays","No birthdays set.",discord.Color.orange()))
            bds.sort(key=lambda x:x.next_bd);ls=[]
            for bd in bds[:count]:
                m=ctx.guild.get_member(bd.user_id)
                if m:
                    ds=self._fd(bd.day,bd.month);du=(bd.next_bd-ist_today()).days
                    st="Today!" if du==0 else "Tomorrow" if du==1 else f"in {du} days"
                    ls.append(f"<:giveaway:1389603154227630193> {m.mention} — {ds} ({st})")
            await ctx.send(embed=self._e("<:Calender:1391669491577917441> Upcoming Birthdays","\n".join(ls),discord.Color.purple()))
        except Exception as e:logger.error(f"Error getting upcoming BDs: {e}");await self._se(ctx,"Failed to get upcoming birthdays.")
    
    @birthday.command(name="setrole")
    @commands.has_permissions(manage_guild=True)
    async def set_role(self,ctx,role:discord.Role,auto_remove:bool=True):
        try:
            s=await self.db.get_gs(ctx.guild.id);s.role_id,s.auto_remove=role.id,auto_remove
            if await self.db.set_gs(s):await self._ss(ctx,f"Birthday role set to {role.mention}\nAuto-remove: {'Yes' if auto_remove else 'No'}")
            else:await self._se(ctx,"Failed to set birthday role.")
        except Exception as e:logger.error(f"Error setting role: {e}");await self._se(ctx,"Failed to set birthday role.")
    
    @birthday.command(name="setchannel")
    @commands.has_permissions(manage_guild=True)
    async def set_channel(self,ctx,channel:discord.TextChannel):
        try:
            s=await self.db.get_gs(ctx.guild.id);s.channel_id=channel.id
            if await self.db.set_gs(s):await self._ss(ctx,f"Birthday announcements → {channel.mention}")
            else:await self._se(ctx,"Failed to set birthday channel.")
        except Exception as e:logger.error(f"Error setting channel: {e}");await self._se(ctx,"Failed to set birthday channel.")
    
    @birthday.command(name="setmessage")
    @commands.has_permissions(manage_guild=True)
    async def set_msg(self,ctx,*,message:str):
        try:
            if len(message)>500:return await self._se(ctx,"Message too long (max 500 chars).")
            s=await self.db.get_gs(ctx.guild.id);s.message_template=message
            if await self.db.set_gs(s):await self._ss(ctx,f"Message template set:\n```{message}```")
            else:await self._se(ctx,"Failed to set message template.")
        except Exception as e:logger.error(f"Error setting message: {e}");await self._se(ctx,"Failed to set birthday message.")
    
    @birthday.command(name="settings")
    @commands.has_permissions(manage_guild=True)
    async def show_settings(self,ctx):
        try:
            s=await self.db.get_gs(ctx.guild.id)
            ri="None set"
            if s.role_id:
                r=ctx.guild.get_role(s.role_id)
                ri=f"{r.mention} (Auto-remove: {'Yes' if s.auto_remove else 'No'})"if r else"<:warning:1389479734823354368> Role not found"
            ci="None set"
            if s.channel_id:
                c=ctx.guild.get_channel(s.channel_id)
                ci=c.mention if c else"<:warning:1389479734823354368> Channel not found"
            await ctx.send(embed=self._e("<a:animated_cake:1391668759152037898> Birthday Settings",f"**Role:** {ri}\n**Channel:** {ci}\n**Message:** ```{s.message_template}```",discord.Color.blue()))
        except Exception as e:logger.error(f"Error showing settings: {e}");await self._se(ctx,"Failed to get settings.")
    
    @birthday.command(name="reset")
    @commands.has_permissions(manage_guild=True)
    async def reset_settings(self,ctx):
        try:
            s=GS(ctx.guild.id)
            if await self.db.set_gs(s):await self._ss(ctx,"Birthday settings reset to default.")
            else:await self._se(ctx,"Failed to reset settings.")
        except Exception as e:logger.error(f"Error resetting settings: {e}");await self._se(ctx,"Failed to reset settings.")

async def setup(bot):await bot.add_cog(Birthday(bot))