import discord
import json
import os
import re
import sys

from discord.ext import commands

kIntents = discord.Intents.default()
kIntents.members = True

cAmongUsCodesChannelName = "among-us-codes"
cCommandRoot = "au"
cCommandJoin = "join"
cCommandLeave = "leave"
cCommandNewGame = "newgame"
cModRolePrefix = "mod"

with open('config.json') as file:
  kConfig = json.load(file)

kUniversalSuffix = kConfig["universalSuffix"]
kAmongUsRoleName = "among-us{}".format(kUniversalSuffix)
kBotChannelName = "notk-bot{}".format(kUniversalSuffix)
kLogChannelName = "{}-log".format(kBotChannelName)

bot = commands.Bot(command_prefix=kConfig["commandPrefix"], intents=kIntents)

cCommandBase = "{}{}".format(bot.command_prefix, cCommandRoot)

cAmongUsJoinRequestMessageText = "{} {}".format(cCommandBase, cCommandJoin)
cAmongUsLeaveRequestMessageText = "{} {}".format(cCommandBase, cCommandLeave)
cAmongUsSendGameNotificationText = "Type `{} {} <room-code>` in any public channel to send a new game notification.".format(cCommandBase, cCommandNewGame)

guilds = {}

########################################################################################################################
# Logging
########################################################################################################################

async def serverLog(ctx, msg):
  print("{}| {}.{}: {}".format(kBotChannelName.upper(), ctx.guild.name, ctx.author.name, msg))

async def log(ctx, guild, msg):
  serverLog(ctx, msg)
  if bool(guild.channelLog):
    await guild.channelLog.send(content="{}".format("{}: {}".format(ctx.author.name, msg)))

async def info(ctx, guild, msg):
  await log(ctx, guild, "INFO: {}".format(msg))

async def sevLog(ctx, guild, msg):
  serverLog(ctx, msg)
  if bool(guild.channelLog):
    await guild.channelLog.send(content="{}: {}".format(ctx.author.mention, msg))
  else:
    await ctx.author.send(msg)

async def warn(ctx, guild, msg):
  await sevLog(ctx, guild, "WARNING: {}".format(msg))

async def err(ctx, guild, msg):
  msg = "ERROR: {}".format(msg)
  await sevLog(ctx, guild, msg)
  raise Exception(msg)

########################################################################################################################
# End Logging
########################################################################################################################

########################################################################################################################
# Startup, setup, and bot functions
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

async def startup(ctx):
  global guilds

  if ctx.guild.id in guilds:
    return

  guilds[ctx.guild.id] = NotkBotGuild()

  # TODO delete
  # for role in ctx.guild.roles:
  #   if role.name == kAmongUsRoleName:
  #     await role.delete(reason="cleanup")

  roleMod = None
  for role in ctx.guild.roles:
    if role.name.startswith(cModRolePrefix):
      roleMod = role
    elif role.name == kAmongUsRoleName:
      guilds[ctx.guild.id].roleAmongUs = role
    else:
      continue
    await info(ctx, guilds[ctx.guild.id], 'Found role: {}'.format(role.name))

  await info(ctx, guilds[ctx.guild.id], "Setting up {}".format(ctx.guild.name))

  # TODO Enable, but avoid sending messages to just whoever sent the command
  # if bool(roleMod) == False:
  #   await warn(ctx, guilds[ctx.guild.id], "{} role not found.".format(cModRolePrefix))

  if bool(guilds[ctx.guild.id].roleAmongUs) == False:
    await info(ctx, guilds[ctx.guild.id], 'Creating {} role'.format(kAmongUsRoleName))
    guilds[ctx.guild.id].roleAmongUs = await ctx.guild.create_role(\
      name=kAmongUsRoleName,\
      mentionable=True,\
      hoist=False,\
      reason="Allow users to easily ping everyone interested in playing Among Us.")
      #colour=Colour.gold,\

  amongUsRoleMessageText = \
  """⚠ notk-bot Instructions ⚠
Type `{}` in any public channel to be notified about NOTK Among Us game sessions.
Type `{}` in any public channel if you no longer want to be notified.
{}
Tag the `{}` role to ping all Among Us players like so: {}""".format(\
    cAmongUsJoinRequestMessageText,\
    cAmongUsLeaveRequestMessageText,\
    cAmongUsSendGameNotificationText,\
    kAmongUsRoleName,\
    guilds[ctx.guild.id].roleAmongUs.mention)

  for channel in ctx.guild.channels:
    if channel.name == kBotChannelName:
      guilds[ctx.guild.id].channelBot = channel
    elif channel.name == kLogChannelName:
      guilds[ctx.guild.id].channelLog = channel
    else:
      continue
    await info(ctx, guilds[ctx.guild.id], 'Found channel: {}'.format(channel.name))

  # TODO delete
  # if bool(guilds[ctx.guild.id].channelBot):
  #   await guilds[ctx.guild.id].channelBot.delete(reason="pre-setup")
  #   guilds[ctx.guild.id].channelBot = None

  amongUsRoleMessage = None
  if bool(guilds[ctx.guild.id].channelBot):
    for message in await guilds[ctx.guild.id].channelBot.history(limit=200).flatten():
      if message.author.id == bot.user.id:
        if message.content == amongUsRoleMessageText:
          await info(ctx, guilds[ctx.guild.id], 'Found {} instructional message in #{}'.format(message.author.name, guilds[ctx.guild.id].channelBot.name))
          amongUsRoleMessage = message
        elif message.content.startswith("⚠ notk-bot Instructions ⚠"):
          await info(ctx, guilds[ctx.guild.id], 'Deleting old message by {} in #{}'.format(message.author.name, guilds[ctx.guild.id].channelBot.name))
          await message.delete()
        #else:
          #info(ctx, guilds[ctx.guild.id], "Found message: {}".format(message.content))
      #else:
        #info(ctx, guilds[ctx.guild.id], "Found message: {}".format(message.content))
  else:
    await info(ctx, guilds[ctx.guild.id], 'Creating bot channel: {}'.format(kBotChannelName))
    overwrites = {
      ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
      ctx.guild.me: discord.PermissionOverwrite(\
        manage_messages=True,\
        read_messages=True,\
        send_messages=True)
    }
    guilds[ctx.guild.id].channelBot = await ctx.guild.create_text_channel(\
      name=kBotChannelName,\
      overwrites=overwrites,\
      topic="NOTK Bot",\
      reason="Need a place to put our instructional message and send join/leave notifications")

    await guilds[ctx.guild.id].channelBot.send(content="{}{}{} has added support for the Among Us player group via the {} role.".format(\
      roleMod.mention if bool(roleMod) else "",\
      ", " if bool(roleMod) else "",\
      bot.user.mention,\
      guilds[ctx.guild.id].roleAmongUs.mention))

  if bool(guilds[ctx.guild.id].channelLog) == False:
    await info(ctx, guilds[ctx.guild.id], 'Creating bot log channel: {}'.format(kLogChannelName))
    overwrites = {
      ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
      ctx.guild.me: discord.PermissionOverwrite(\
        manage_messages=True,\
        read_messages=True,\
        send_messages=True)
    }
    guilds[ctx.guild.id].channelLog = await ctx.guild.create_text_channel(\
      name=kLogChannelName,\
      overwrites=overwrites,\
      topic="NOTK Bot Log",\
      reason="Need a place to put logs")

  if amongUsRoleMessage == None:
    await info(ctx, guilds[ctx.guild.id], 'Sending {} instructional message'.format(kAmongUsRoleName))
    amongUsRoleMessage = await guilds[ctx.guild.id].channelBot.send(content=amongUsRoleMessageText)
  
  if amongUsRoleMessage.pinned == True:
    await info(ctx, guilds[ctx.guild.id], '{} instructional message already pinned.'.format(kAmongUsRoleName))
  else:
    await info(ctx, guilds[ctx.guild.id], 'Pinning {} instructional message'.format(kAmongUsRoleName))
    await amongUsRoleMessage.pin(reason="The {} instructional message needs to be very visible to be useful".format(kBotChannelName))

########################################################################################################################
# End Startup, setup, and bot functions
########################################################################################################################

########################################################################################################################
# Bot Commands
########################################################################################################################

@bot.command()
async def au(ctx, cmd, *args):
  await startup(ctx)

  await serverLog(ctx, guilds[ctx.guild.id], "Processing `{}` command. Args: `{}`".format(cmd, "`, `".join(args)))

  members = []
  memberNames = []
  resolved = []
  if cmd in [ cCommandJoin, cCommandLeave]:
    if len(args) > 0:
      userIDs = {}
      userNames = []
      for arg in args:
        if arg.startswith('<@') & arg.endswith('>'):
          userID = arg[2:-1];
          if userID.startswith('!'):
            userID = userID[1:len(userID)];
          userIDs[userID] = arg
        else:
          userNames.append(arg)
      for userID in userIDs:
        try:
          member = await ctx.guild.fetch_member(userID)
        except Exception as e:
          await warn(ctx, guilds[ctx.guild.id], "userID {}: {}".format(userID, str(e)))
        except:
          await warn(ctx, guilds[ctx.guild.id], "userID {}: {}".format(userID, str(sys.exc_info()[0])))
        else:
          if member.name not in memberNames:
            resolved.append(userIDs[userID])
            members.append(member)
            memberNames.append(member.name)
      fetchedMemberCount = 0
      while (fetchedMemberCount < ctx.guild.member_count) & (len(userNames) > len(members)):
        for member in await ctx.guild.fetch_members(limit=None).flatten():
          # await info(ctx, guilds[ctx.guild.id], "Fetched {}".format(member.name))
          fetchedMemberCount += 1
          psuedoName = member.name.replace(" ", "")
          if member.name in userNames:
            psuedoName = member.name
          if psuedoName in userNames &\
             member.name not in memberNames:
            resolved.append(psuedoName)
            members.append(member)
            memberNames.append(member.name)
    else:
      member = await ctx.guild.fetch_member(ctx.author.id)
      members = [member]
      memberNames = [member.name]
    missing = set(args) - set(resolved)
    if (len(missing) > 0):
      await warn(ctx, guilds[ctx.guild.id], "Could not find `{}` members: `{}`!".format(ctx.guild.name, "`, `".join(missing)))

  if cmd == cCommandJoin:
    await guilds[ctx.guild.id].addAmongUsPlayer(ctx, members)
  elif cmd == cCommandLeave:
    await guilds[ctx.guild.id].removeAmongUsPlayer(ctx, members)
  elif cmd == cCommandNewGame:
    await guilds[ctx.guild.id].notifyAmongUsGame(ctx, ctx.message.channel, args[0])
  else:
    await err(ctx, "Invalid command `{}`.".format(cmd))

class NotkBotGuild:
  def __init__(self):
    self.channelBot = None
    self.channelLog = None
    self.roleAmongUs = None

  async def addAmongUsPlayer(self, ctx, members):
    alreadyMemberNames = []
    for member in members:
      if self.roleAmongUs in member.roles:
        alreadyMemberNames.append(member.name)
      else:
        await info(ctx, self, "Adding {} to the {} players".format(member.name, self.roleAmongUs.name))
        await member.add_roles(\
          self.roleAmongUs,\
          reason="{} requested for {} to be pinged regarding Among Us games".format(\
            ctx.author.name,\
            member.name))
        await self.channelBot.send(\
          content="Hey {} players! {} is now among the Among Us players!".format(\
            self.roleAmongUs.mention,\
            member.mention))
        await member.send(\
          content="You have been added to {}'s Among Us players. Type `{}` in any public channel in {} to leave the Among Us players.".format(\
            ctx.guild.name,\
            cAmongUsLeaveRequestMessageText,\
            ctx.guild.name))
    if (len(alreadyMemberNames) > 0):
      await warn(ctx, self, "{} {} already among the {} players".format(\
        ", ".join(alreadyMemberNames),\
        "is" if len(alreadyMemberNames) == 1 else "are",\
        self.roleAmongUs.name))

  async def removeAmongUsPlayer(self, ctx, members):
    missingMemberNames = []
    for member in members:
      if self.roleAmongUs in member.roles:
        await info(ctx, self, "Removing {} from the {} players".format(member.name, self.roleAmongUs.name))
        await member.remove_roles(\
          self.roleAmongUs,\
          reason="{} requested for {} to no longer receive pings regarding Among Us games".format(\
            ctx.author.name,\
            member.name))
        await self.channelBot.send(content="{} is now Among The Hidden.".format(member.mention))
      else:
        missingMemberNames.append(member.name)
    if (len(missingMemberNames) > 0):
      await warn(ctx, self, "{} isn't among the {} players".format(\
        ", ".join(missingMemberNames),\
        self.roleAmongUs.name))

  async def notifyAmongUsGame(self, ctx, channel, code):
    match = re.compile(r'^([A-Za-z]{6})$').search(code)
    if bool(match) == False:
      await err(ctx, self, "Bad room code `{}`. Must be six letters.".format(code))
    code = code.upper()
    await info(ctx, self, "Notifying {} of Among Us game code {} in channel {}".format(self.roleAmongUs.name, code, channel.name))
    await channel.send(\
      content="Attention {}! New game code: `{}`. Type `{}` if you no longer want receive these notifications. {}".format(\
        self.roleAmongUs.mention,\
        code,\
        cAmongUsLeaveRequestMessageText,\
        cAmongUsSendGameNotificationText))
  #  codeSpelled = re.sub(r"([A-Z])", r"\1 ", code)
  #  await channel.send(content="New game code: `{}`.".format(codeSpelled),\
  #                     tts=True)

########################################################################################################################
# End Bot Commands
########################################################################################################################

boot()
