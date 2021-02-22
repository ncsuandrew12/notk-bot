import discord
import inspect
import json
import os
import re
import sys

from discord.ext import commands

# Get function name
#import inspect
# inspect.currentframe().f_code.co_name

# Needed to be able to list members (for mapping member name arguments to actual members)
kIntents = discord.Intents.default()
kIntents.members = True

cAmongUsCodesChannelName = "among-us-codes"
cCommandRoot = "au" # Must match the @bot.commmand() function name
cCommandJoin = "join"
cCommandLeave = "leave"
cCommandNewGame = "newgame"
cRoleModPrefix = "mod"
cRoleModSubstring = "moderator"

with open('config.json') as file:
  kConfig = json.load(file)

cUniversalSuffix = kConfig["universalSuffix"]
cBotName = "notk-bot{}".format(cUniversalSuffix)
cAmongUsRoleName = "among-us{}".format(cUniversalSuffix)
cBotChannelName = cBotName
cLogChannelName = "{}-log".format(cBotChannelName)

bot = commands.Bot(command_prefix=kConfig["commandPrefix"], intents=kIntents)

cCommandBase = "{}{}".format(bot.command_prefix, cCommandRoot)

cAmongUsJoinRequestMessageText = "{} {}".format(cCommandBase, cCommandJoin)
cAmongUsLeaveRequestMessageText = "{} {}".format(cCommandBase, cCommandLeave)
cAmongUsSendGameNotificationText = "Type `{} {} <room-code>` in any public channel to send a new game notification.".format(cCommandBase, cCommandNewGame)

guildBots = {}

########################################################################################################################
# Exceptions
########################################################################################################################

class MinorException(Exception):
  def __init__(self, msg):
    Exception.__init__(self, msg)

########################################################################################################################
# End Exceptions
########################################################################################################################

########################################################################################################################
# Basic Logging
########################################################################################################################

def log(msg):
  print("{}| {}".format(cBotName.upper(), msg))

def logDebug(msg):
  log("DEBUG:   {}".format(msg))

########################################################################################################################
# End Basic Logging
########################################################################################################################

########################################################################################################################
# Discord Logging
########################################################################################################################

def dServerLog(ctx, msg):
  log("{}.{}: {}".format(ctx.guild.name, ctx.author.name, msg))

async def dLog(guildBot, ctx, msg):
  dServerLog(ctx, msg)
  if bool(guildBot.channelLog):
    await guildBot.channelLog.send(content="{}".format("{}: {}".format(ctx.author.name, msg)))

async def dLogErr(guildBot, ctx, msg):
  await dLogSevere(guildBot, ctx, "ERROR:   {}".format(msg))

async def dLogWarn(guildBot, ctx, msg):
  await dLogSevere(guildBot, ctx, "WARNING: {}".format(msg))

async def dLogSevere(guildBot, ctx, msg):
  dServerLog(ctx, msg)
  if bool(guildBot.channelLog):
    await guildBot.channelLog.send(\
      content="{}: {}".format(\
        ctx.author.mention if bool(ctx.author.mention) else ctx.author.name,\
        msg))
  else:
    await ctx.author.send(msg)

async def dLogInfo(guildBot, ctx, msg):
  await dLog(guildBot, ctx, "INFO:    {}".format(msg))

def dLogDebug(ctx, msg):
  dServerLog(ctx, "DEBUG:   {}".format(msg))

########################################################################################################################
# End Discord Logging
########################################################################################################################

########################################################################################################################
# Discord Error
########################################################################################################################

async def dErr(guildBot, ctx, msg):
  await dLogErr(guildBot, ctx, msg)
  raise Exception(msg)

async def dErrMinor(guildBot, ctx, msg):
  await dLogErr(guildBot, ctx, msg)
  raise MinorException(msg)

########################################################################################################################
# End Discord Error
########################################################################################################################

########################################################################################################################
# Bot
########################################################################################################################

def boot():
  tokenFilePath = 'discord.token'
  if os.path.exists(tokenFilePath):
    tokenFile = open(tokenFilePath, 'r')
    try:
      token = tokenFile.readline()
    finally:
      tokenFile.close()
  else:
    token = os.getenv('TOKEN')
  bot.run(token)

@bot.event
async def on_ready():
  global guildBots

  logDebug("Starting {} bots".format(len(bot.guilds)))

  for guild in bot.guilds:
    if guild.id in guildBots:
      continue

    guildBot = GuildBot()
    await guildBot.setup(guild)
    guildBots[guild.id] = guildBot

  logDebug("{} bots running".format(len(guildBots)))

@bot.command()
async def au(ctx, cmd, *args):
  global guildBots

  try:
    if ctx.guild.id not in guildBots:
      await dErr(ctx, None, "`{}` has not been setup yet. This shouldn't be possible. Please contact the bot developer ({})".format(\
        ctx.guild.name,
        "andrewf#6219"))

    guildBot = guildBots[ctx.guild.id]
    dLogDebug(ctx, "Processing `{}` command. Args: `{}`".format(cmd, "`, `".join(args)))

    members = []
    memberNames = []
    resolved = []
    if cmd in [ cCommandJoin, cCommandLeave]:
      if len(args) > 0:
        userIDs = {}
        userNames = []
        for arg in args:
          if arg.startswith('<@') & arg.endswith('>'):
            userID = arg[2:-1]
            while userID.startswith('!') | userID.startswith('&'):
              userID = userID[1:len(userID)]
            userIDs[userID] = arg
          else:
            userNames.append(arg)
        for userID in userIDs:
          try:
            member = await ctx.guild.fetch_member(userID)
          except Exception as e:
            await dLogWarn(guildBot, ctx, "userID `{}`: {}".format(userID, str(e)))
          except:
            await dLogWarn(guildBot, ctx, "userID `{}`: {}".format(userID, str(sys.exc_info()[0])))
          else:
            if member.name not in memberNames:
              resolved.append(userIDs[userID])
              members.append(member)
              memberNames.append(member.name)
        fetchedMemberCount = 0
        while (fetchedMemberCount < ctx.guild.member_count) & (len(userNames) > len(members)):
          for member in await ctx.guild.fetch_members(limit=None).flatten():
            # await dLogInfo(guildBot, ctx, "Fetched {}".format(member.name))
            fetchedMemberCount += 1
            psuedoName = member.name.replace(" ", "")
            if member.name in userNames:
              psuedoName = member.name
            if bool(psuedoName in userNames) &\
              bool(member.name not in memberNames):
              resolved.append(psuedoName)
              members.append(member)
              memberNames.append(member.name)
      else:
        member = await ctx.guild.fetch_member(ctx.author.id)
        members = [member]
        memberNames = [member.name]
      missing = set(args) - set(resolved)
      if (len(missing) > 0):
        await dLogWarn(guildBot, ctx, "Could not find `{}` members: `{}`!".format(ctx.guild.name, "`, `".join(missing)))

    if cmd == cCommandJoin:
      await guildBot.addAmongUsPlayer(ctx, members)
    elif cmd == cCommandLeave:
      await guildBot.removeAmongUsPlayer(ctx, members)
    elif cmd == cCommandNewGame:
      await guildBot.notifyAmongUsGame(ctx, ctx.message.channel, args[0])
    else:
      await dErr(guildBot, ctx, "Invalid command `{}`.".format(cmd))
  except MinorException as e:
    # This error will have already been logged
    # TODO better way to noop?
    someVar = None
  except:
    raise

########################################################################################################################
# End Bot
########################################################################################################################

########################################################################################################################
# GuildBot
########################################################################################################################
class GuildBot:
  def __init__(self):
    self.channelBot = None
    self.channelLog = None
    self.roleAmongUs = None

  async def setup(self, guild):
    roleMod = None

    ctx = ContextStubbed(guild, AuthorStubbed(guild.name))

    dLogDebug(ctx, "Starting bot (before channel located)")

    for channel in guild.channels:
      if channel.name == cBotChannelName:
        self.channelBot = channel
      elif channel.name == cLogChannelName:
        self.channelLog = channel
      else:
        continue
      dLogDebug(ctx, 'Found: `#{}`'.format(channel.name))

    # TODO delete
    # if bool(self.channelBot):
    #   await self.channelBot.delete(reason="pre-setup")
    #   guildBot.channelBot = None

    if bool(self.channelLog) == False:
      dLogDebug(ctx, 'Creating bot log: `#{}`'.format(cLogChannelName))
      overwrites = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False),
        guild.me: discord.PermissionOverwrite(\
          manage_messages=True,\
          read_messages=True,\
          send_messages=True)
      }
      self.channelLog = await guild.create_text_channel(\
        name=cLogChannelName,\
        overwrites=overwrites,\
        topic="NOTK Bot Log",\
        reason="Need a place to put logs")

    await self.dLogInfo(ctx, "Starting bot")

    # TODO delete
    # for role in ctx.guild.roles:
    #   if role.name == cAmongUsRoleName:
    #     await role.delete(reason="cleanup")

    for role in guild.roles:
      if bool(roleMod) & \
         (role.name.lower().startswith(cRoleModPrefix.lower()) |\
          bool(cRoleModSubstring.lower() in role.name.lower())):
        roleMod = role
      elif role.name == cAmongUsRoleName:
        self.roleAmongUs = role
      else:
        continue
      await self.dLogInfo(ctx, 'Found: `@{}`'.format(role.name))

    # TODO Enable, but avoid sending messages to just whoever sent the command
    # if bool(roleMod) == False:
    #   await dLogWarn(self, "{} role not found.".format(cRoleModPrefix))

    if bool(self.roleAmongUs) == False:
      await self.dLogInfo(ctx, 'Creating `@{}`'.format(cAmongUsRoleName))
      self.roleAmongUs = await guild.create_role(\
        name=cAmongUsRoleName,\
        mentionable=True,\
        hoist=False,\
        reason="Allow users to easily ping everyone interested in playing Among Us.")
        #colour=Colour.gold,\

    amongUsRoleMessageText = \
    """⚠ notk-bot Instructions ⚠
Type `{}` in any public channel to be notified about NOTK Among Us game sessions.
Type `{}` in any public channel if you no longer want to be notified.
{}
Tag the `{}` role to ping all Among Us players like so: {}
I recommend muting the {} channel; it is only for logging purposes and will be very noisy.""".format(\
      cAmongUsJoinRequestMessageText,\
      cAmongUsLeaveRequestMessageText,\
      cAmongUsSendGameNotificationText,\
      cAmongUsRoleName,\
      self.roleAmongUs.mention,
      self.channelLog.mention)

    amongUsRoleMessage = None
    if bool(self.channelBot):
      for message in await self.channelBot.history(limit=200).flatten():
        if message.author.id == bot.user.id:
          if message.content == amongUsRoleMessageText:
            await self.dLogInfo(ctx, 'Found `{}` instructional message in `#{}`'.format(message.author.name, self.channelBot.name))
            amongUsRoleMessage = message
          # elif message.content.startswith("⚠ notk-bot Instructions ⚠"):
            # await self.dLogInfo(ctx, 'Deleting old message by `@{}` in `#{}`'.format(message.author.name, self.channelBot.name))
            # await message.delete()
          #else:
            #dLogInfo(ctx, guildBot, "Found message: {}".format(message.content))
        #else:
          #dLogInfo(ctx, guildBot, "Found message: {}".format(message.content))
    else:
      await self.dLogInfo(ctx, 'Creating bot channel: `#{}`'.format(cBotChannelName))
      overwrites = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False),
        guild.me: discord.PermissionOverwrite(\
          manage_messages=True,\
          read_messages=True,\
          send_messages=True)
      }
      self.channelBot = await guild.create_text_channel(\
        name=cBotChannelName,\
        overwrites=overwrites,\
        topic="NOTK Bot",\
        reason="Need a place to put our instructional message and send join/leave notifications")

      await self.channelBot.send(content="{}{}{} has added support for the Among Us player group via the `@{}` role.".format(\
        roleMod.mention if bool(roleMod) else "",\
        ", " if bool(roleMod) else "",\
        bot.user.mention,\
        self.roleAmongUs.mention))

    if amongUsRoleMessage == None:
      await self.dLogInfo(ctx, 'Sending `{}` instructional message'.format(cAmongUsRoleName))
      amongUsRoleMessage = await self.channelBot.send(content=amongUsRoleMessageText)
    
    if amongUsRoleMessage.pinned == True:
      await self.dLogInfo(ctx, '`{}` instructional message already pinned.'.format(cAmongUsRoleName))
    else:
      await self.dLogInfo(ctx, 'Pinning {} instructional message'.format(cAmongUsRoleName))
      await amongUsRoleMessage.pin(reason="The `{}` instructional message needs to be very visible to be useful".format(cBotName))

    await self.dLogInfo(ctx, "Bot started.")

  async def addAmongUsPlayer(self, ctx, members):
    alreadyMemberNames = []
    for member in members:
      if self.roleAmongUs in member.roles:
        alreadyMemberNames.append(member.name)
      else:
        await self.dLogInfo(ctx, "Adding `@{}` to the `@{}` players".format(member.name, self.roleAmongUs.name))
        await member.add_roles(\
          self.roleAmongUs,\
          reason="{} requested for {} to be pinged regarding Among Us games".format(\
            ctx.author.name,\
            member.name))
        await self.channelBot.send(\
          content="Hey {} players! {} is now among the Among Us players!".format(\
            self.roleAmongUs.mention,\
            member.mention))
        # TODO skip this if the recipient is the bot (i.e. it's trying to message itself)
        await member.send(\
          content="You have been added to `{}`'s Among Us players. Type `{}` in any public channel in `{}` to leave the Among Us players.".format(\
            ctx.guild.name,\
            cAmongUsLeaveRequestMessageText,\
            ctx.guild.name))
    if (len(alreadyMemberNames) > 0):
      await dLogWarn(self, ctx, "`@{}` {} already among the `@{}` players".format(\
        "`, `@".join(alreadyMemberNames),\
        "is" if len(alreadyMemberNames) == 1 else "are",\
        self.roleAmongUs.name))

  async def removeAmongUsPlayer(self, ctx, members):
    missingMemberNames = []
    for member in members:
      if self.roleAmongUs in member.roles:
        await self.dLogInfo(ctx, "Removing `@{}` from the `{}` players".format(member.name, self.roleAmongUs.name))
        await member.remove_roles(\
          self.roleAmongUs,\
          reason="{} requested for {} to no longer receive pings regarding Among Us games".format(\
            ctx.author.name,\
            member.name))
        await self.channelBot.send(content="{} is now Among The Hidden.".format(member.mention))
        await member.send(content="You have been remove from `{}`'s Among Us players.".format(ctx.guild.name))
      else:
        missingMemberNames.append(member.name)
    if (len(missingMemberNames) > 0):
      await self.dLogWarn(ctx, "{} isn't among the {} players".format(\
        ", ".join(missingMemberNames),\
        self.roleAmongUs.name))

  async def notifyAmongUsGame(self, ctx, channel, code):
    match = re.compile(r'^([A-Za-z]{6})$').search(code)
    if bool(match) == False:
      await self.dErrMinor(ctx, "Bad room code `{}`. Must be six letters.".format(code))
    code = code.upper()
    await self.dLogInfo(ctx, "Notifying `@{}` of Among Us game code `{}` in `#{}`".format(self.roleAmongUs.name, code, channel.name))
    await channel.send(\
      content="Attention {}! New game code: `{}`. Type `{}` if you no longer want receive these notifications. {}".format(\
        self.roleAmongUs.mention,\
        code,\
        cAmongUsLeaveRequestMessageText,\
        cAmongUsSendGameNotificationText))
  #  codeSpelled = re.sub(r"([A-Z])", r"\1 ", code)
  #  await channel.send(content="New game code: `{}`.".format(codeSpelled),\
  #                     tts=True)

  async def dLogInfo(self, ctx, msg):
    await dLogInfo(self, ctx, msg)

  async def dLogWarn(self, ctx, msg):
    await dLogWarn(self, ctx, msg)

  async def dErr(self, ctx, msg):
    await dErr(self, ctx, msg)

  async def dErrMinor(self, ctx, msg):
    await dErrMinor(self, ctx, msg)

########################################################################################################################
# End GuildBot
########################################################################################################################

########################################################################################################################
# Discord Facsimilies classes so we can use the common logging functions
########################################################################################################################
class AuthorStubbed:
  def __init__(self, guildName):
    self.guildName = guildName
    self.mention = None
    self.name = cBotName
  
  async def send(self, msg):
    print("{}| {}.{}: \"sending\" to fake author: {}".format(cBotName.upper(), self.guildName, self.name, msg))

class ContextStubbed:
  def __init__(self, guild, author):
    self.author = author
    self.guild = guild
########################################################################################################################
# End Discord Facsimilies
########################################################################################################################

boot()