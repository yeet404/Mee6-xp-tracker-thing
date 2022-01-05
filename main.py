from datetime import datetime
import asyncio
from mee6_py_api import API
import discord
from discord.ext import tasks
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True

mee6API = API(os.environ['API'])

client = commands.Bot(intents=intents, command_prefix = '$')

class person():
  def __init__(self, name, userid, xplist, hourlyxp, dailyxp, weeklyxp, totalxp):
    self.name=name
    self.userid=userid
    self.xplist=list(xplist)
    self.hourlyxp=hourlyxp
    self.dailyxp=dailyxp
    self.weeklyxp=weeklyxp
    self.totalxp=totalxp
  
  def gethourlyxp(self):
    self.hourlyxp=self.xplist[-1]-self.xplist[-2]

  def getdailyxp(self):
    self.dailyxp=self.xplist[-1]-self.xplist[-24]

  def getweeklyxp(self):
    self.weeklyxp=self.xplist[-1]-self.xplist[0]

  #function to clear xp list
  def clear(self):
    self.xplist=self.xplist.clear()

#dictionary to put members in
people={}

@client.event
async def on_ready():
  print('Logged in as {0.user}'.format(client))

async def xp_thing():
  global people
  await client.wait_until_ready()
  #getting channel to send messages in
  channel=client.get_channel(id=os.environ['CHANNELID'])
  #setting up dictionary
  leaderboard_page = await mee6API.levels.get_leaderboard_page(0)
  for x in range(len(leaderboard_page['players'])):
    people[leaderboard_page['players'][x]['id']]=person(leaderboard_page['players'][x]['username'], leaderboard_page['players'][x]['id'], [], 1, 1, 1, leaderboard_page['players'][x]['xp'])
    firstRun=True
    firstBotRun=True
  while not client.is_closed():
    #skipping minute wait when first starting
    if firstRun:
      firstRun=False
      pass
    #waiting a minute for each loop
    else:
      await asyncio.sleep(30)
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    current_minute=now.strftime("%M")
    current_hour=now.strftime("%H")
    print(current_hour)
    if current_minute!="00":
      run=False
      continue
    elif current_minute=="00":
      #waiting until 12 AM est to start bot
      if firstBotRun:
        if current_hour=="05":
          firstBotRun=False
          pass
        else:
          continue
      #waiting every hour until running bot
      else:
        #don't want to run twice (sleep is less than a minute)
        if not run:
          pass
        elif run:
          continue
    equalsWeekly=False
    equalsDaily=False
    equalsHourly=False
    hourlyMessage=''
    dailyMessage=''
    weeklyMessage=''
    dailyDaysToCatchMessage=''
    weeklyDaysToCatchMessage=''
    leaderboard_page = await mee6API.levels.get_leaderboard_page(0)
    #calculating xp rate
    for thing in range(len(leaderboard_page['players'])):
      personId=(leaderboard_page['players'][thing]['id'])
      #appending total xp to xplist
      xp = leaderboard_page['players'][thing]['xp']
      people[personId].xplist.append(xp)
      #setting total xp
      people[personId].totalxp=xp
      #skipping first run
      if len(people[personId].xplist)==1:
        pass
      #getting daily xp
      if len(people[personId].xplist)%24==0:
        people[personId].getdailyxp()
        equalsDaily=True
      #getting hourly xp
      if len(people[personId].xplist)>1 and not firstBotRun:
        people[personId].gethourlyxp()
        equalsHourly=True
      #getting weekly xp
      if len(people[personId].xplist)==168:
        people[personId].getweeklyxp()
        equalsWeekly=True
        people[personId].clear()
    if equalsHourly:
      #sending messages
      peopleHourly=sorted(people, key = lambda name: people[name].hourlyxp, reverse=True)
      for thing in peopleHourly:
        if people[thing].hourlyxp!=0:
          hourlyMessage+=f"{people[thing].name}'s hourly xp is {people[thing].hourlyxp}. \n"
    if equalsDaily:
      #sending messages
      peopleDaily=sorted(people, key = lambda name: people[name].dailyxp, reverse=True)
      for thing in peopleDaily:
        if people[thing].dailyxp!=0:
          dailyMessage+=f"{people[thing].name}'s daily xp is {people[thing].dailyxp}. \n"
      #calculating days to catch up
      totalXp=sorted(people, key = lambda name: people[name].totalxp, reverse=True)
      totalXpList=list(totalXp)
      for x in range(len(totalXpList)-1):
        p1=totalXpList[x]
        p2=totalXpList[x+1]
        if people[p1].dailyxp<people[p2].dailyxp:
          totalXpDifference=people[p1].totalxp-people[p2].totalxp
          dailyXpDifference=people[p2].dailyxp-people[p1].dailyxp
          daysToCatch=totalXpDifference//dailyXpDifference
          dailyDaysToCatchMessage+=(f"{people[p2].name} will pass {people[p1].name} in {daysToCatch} days at the current xp gain rate. \n")
    if equalsWeekly:
      peopleWeekly=sorted(people, key = lambda name: people[name].weeklyxp, reverse=True)
      for thing in peopleWeekly:
        if people[thing].weeklyxp!=0:
          weeklyMessage+=f"{people[thing].name}'s weekly xp is {people[thing].weeklyxp}. \n"
      #calculating days to catch
      totalXp=sorted(people, key = lambda name: people[name].totalxp, reverse=True)
      totalXpList=list(totalXp)
      for x in range(len(totalXpList)-1):
        p1=totalXpList[x]
        p2=totalXpList[x+1]
        if people[p1].weeklyxp<people[p2].weeklyxp:
          totalXpDifference=people[p1].totalxp-people[p2].totalxp
          weeklyXpDifference=people[p2].weeklyxp-people[p1].weeklyxp
          daysToCatch=totalXpDifference//weeklyXpDifference
          weeklyDaysToCatchMessage+=(f"{people[p2].name} will pass {people[p1].name} in {daysToCatch} days at the current xp gain rate. \n")
    #sending messages
    if equalsHourly:
      if not hourlyMessage:
        embed=discord.Embed(title='Hourly XP', description=hourlyMessage, color=discord.Colour.blue())
        await channel.send(embed=embed)
      else:
        embed=discord.Embed(title='Hourly XP', description="No one gained xp in the last hour \n", color=discord.Colour.red())
        await channel.send(embed=embed)
    if equalsDaily:
      if not dailyMessage:
        embed=discord.Embed(title='Daily XP', description=dailyMessage, color=discord.Colour.green())
        await channel.send(embed=embed)
      else:
        embed=discord.Embed(title='Daily XP', description="No one gained xp in the last day \n", color=discord.Colour.green())
        await channel.send(embed=embed)
      if not dailyDaysToCatchMessage:
        embed=discord.Embed(title='Days to Catch (Daily)', description=dailyDaysToCatchMessage, color=discord.Colour.green())
        await channel.send(embed=embed)
      else:
        embed=discord.Embed(title='Days to Catch (Daily)', description="No one is going to catch up \n", color=discord.Colour.red())
        await channel.send(embed=embed)
    if equalsWeekly:
      if not weeklyMessage:
        embed=discord.Embed(title='Weekly XP', description=weeklyMessage, color=discord.Colour.orange())
        await channel.send(embed=embed)
      else:
        embed=discord.Embed(title='Weekly XP', description="No one gained xp in the past week \n", color=discord.Colour.orange())
        await channel.send(embed=embed)
      if not weeklyDaysToCatchMessage:
        embed=discord.Embed(title='Days to Catch (Weekly)', description=weeklyDaysToCatchMessage, color=discord.Colour.orange())
        await channel.send(embed=embed)
      else:
        embed=discord.Embed(title='Days to Catch (Weekly)', description="No one is going to catch up \n", color=discord.Colour.red())
        await channel.send(embed=embed)
    run=True


client.loop.create_task(xp_thing())
client.run(os.environ['TOKEN'])
