import discord
import os
import re
import sys

from discord.ext import commands

kIntents = discord.Intents.default()
kIntents.members = True

cAmongUsCodesChannelName = "among-us-codes"
cAmongUsRoleName = "among-us"
cAmongUsSendGameNotificationText = ""
cCommandRoot = "au"
cCommandJoin = "join"
cCommandLeave = "leave"
cCommandNewGame = "newgame"
cBotChannelName = "notk-bot"
cModRolePrefix = "mod"

bot = commands.Bot(command_prefix='$', intents=kIntents)

cCommandBase = "{}{}".format(bot.command_prefix, cCommandRoot)

cAmongUsJoinRequestMessageText = "{} {}".format(cCommandBase, cCommandJoin)
cAmongUsLeaveRequestMessageText = "{} {}".format(cCommandBase, cCommandLeave)
cAmongUsSendGameNotificationText = "Type `{} {} <room-code>` in any public channel to send a new game notification.".format(cCommandBase, cCommandNewGame)

guilds = {}

########################################################################################################################
# Logging
########################################################################################################################

def log(ctx, msg):
  print("{}| {}.{}: {}".format(cBotChannelName.upper(), ctx.guild.name, ctx.author.name, msg))

def info(ctx, msg):
  log(ctx, "   INFO: {}".format(msg))

async def warn(ctx, msg):
  log(ctx, "WARNING: {}".format(msg))
  await ctx.author.send(msg)

async def err(ctx, msg):
  msg =    "  ERROR: {}".format(msg)
  log(ctx, msg)
  await ctx.author.send(msg)
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

  # TODO delete
  # for role in ctx.guild.roles:
  #   if role.name == cAmongUsRoleName:
  #     await role.delete(reason="cleanup")

  roleMod = None
  roleAmongUs = None
  for role in ctx.guild.roles:
    if role.name.startswith(cModRolePrefix):
      roleMod = role
    elif role.name == cAmongUsRoleName:
      roleAmongUs = role
    else:
      continue
    info(ctx, 'Found role: {}'.format(role.name))

  info(ctx, "Setting up {}".format(ctx.guild.name))

  if bool(roleMod) == False:
    await warn(ctx, "{} role not found.".format(cModRolePrefix))

  if bool(roleAmongUs) == False:
    info(ctx, 'Creating {} role'.format(cAmongUsRoleName))
    roleAmongUs = await ctx.guild.create_role(\
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
Tag the `{}` role to ping all Among Us players like so: {}""".format(\
    cAmongUsJoinRequestMessageText,\
    cAmongUsLeaveRequestMessageText,\
    cAmongUsSendGameNotificationText,\
    cAmongUsRoleName,\
    roleAmongUs.mention)

  channelBot = None
  for channel in ctx.guild.channels:
    if channel.name == cBotChannelName:
      channelBot = channel
    else:
      continue
    info(ctx, 'Found channel: {}'.format(channel.name))

  # TODO delete
  # if bool(channelBot):
  #   await channelBot.delete(reason="pre-setup")
  #   channelBot = None

  amongUsRoleMessage = None
  if bool(channelBot):
    for message in await channelBot.history(limit=200).flatten():
      if message.author.id == bot.user.id:
        if message.content == amongUsRoleMessageText:
          info(ctx, 'Found {} instructional message in #{}'.format(message.author.name, channelBot.name))
          amongUsRoleMessage = message
        elif message.content.startswith("⚠ notk-bot Instructions ⚠"):
          info(ctx, 'Deleting old message by {} in #{}'.format(message.author.name, channelBot.name))
          await message.delete()
        #else:
          #info(ctx, "Found message: {}".format(message.content))
      #else:
        #info(ctx, "Found message: {}".format(message.content))
  else:
    info(ctx, 'Creating bot channel: {}'.format(cBotChannelName))
    overwrites = {
      ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
      ctx.guild.me: discord.PermissionOverwrite(\
        manage_messages=True,\
        read_messages=True,\
        send_messages=True)
    }
    channelBot = await ctx.guild.create_text_channel(\
      name=cBotChannelName,\
      overwrites=overwrites,\
      topic="NOTK Bot",\
      reason="Need a place to put our message for users to react to")

    await channelBot.send(content="{}{}{} has added support for the Among Us player group via the {} role.".format(\
      roleMod.mention if bool(roleMod) else "",\
      ", " if bool(roleMod) else "",\
      bot.user.mention,\
      roleAmongUs.mention))

  if amongUsRoleMessage == None:
    info(ctx, 'Sending {} instructional message'.format(cAmongUsRoleName))
    amongUsRoleMessage = await channelBot.send(content=amongUsRoleMessageText)
  
  if amongUsRoleMessage.pinned == True:
    info(ctx, '{} instructional message already pinned.'.format(cAmongUsRoleName))
  else:
    info(ctx, 'Pinning {} instructional message'.format(cAmongUsRoleName))
    await amongUsRoleMessage.pin(reason="The {} instructional message needs to be very visible to be useful".format(cBotChannelName))

  guilds[ctx.guild.id] = NotkBot(channelBot, roleAmongUs)

########################################################################################################################
# End Startup, setup, and bot functions
########################################################################################################################

########################################################################################################################
# Bot Commands
########################################################################################################################

@bot.command()
async def au(ctx, cmd, *args):
  await startup(ctx)

  members = []
  if cmd in [ cCommandJoin, cCommandLeave]:
    if len(args) > 0:
      fetchedMemberCount = 0
      while (fetchedMemberCount < ctx.guild.member_count) & (len(args) > len(members)):
        for member in await ctx.guild.fetch_members(limit=100).flatten():
          fetchedMemberCount += 1
          if member.name in args:
            members.append(member)
    else:
      members.append(await ctx.guild.fetch_member(ctx.author.id))

  if cmd == cCommandJoin:
    await guilds[ctx.guild.id].addAmongUsPlayer(ctx, members)
  elif cmd == cCommandLeave:
    await guilds[ctx.guild.id].removeAmongUsPlayer(ctx, members)
  elif cmd == cCommandNewGame:
    await guilds[ctx.guild.id].notifyAmongUsGame(ctx, ctx.message.channel, args[0])
  else:
    await err(ctx, "Invalid command `{}`.".format(cmd))

class NotkBot:
  def __init__(self, channelBot, roleAmongUs):
    self.channelBot = channelBot
    self.roleAmongUs = roleAmongUs

  async def addAmongUsPlayer(self, ctx, members):
    for member in members:
      info(ctx, "amf add {}".format(member.name))
      if self.roleAmongUs in member.roles:
        await warn(ctx, "{} is already among the {} players".format(member.name, role.name))
      else:
        info(ctx, "Adding {} to the {} players".format(member.name, self.roleAmongUs.name))
        await member.add_roles(\
          self.roleAmongUs,\
          reason="{} requested to be pinged regarding Among Us games".format(member.name))
        await self.channelBot.send(\
          content="Hey {} players! {} is now among the Among Us players!".format(\
            self.roleAmongUs.mention,\
            member.mention))
        await member.send(\
          content="You have been added to {}'s Among Us players. Type `{}` in any public channel in {} to leave the Among Us players.".format(\
            ctx.guild.name,\
            cAmongUsLeaveRequestMessageText,\
            ctx.guild.name))

  async def removeAmongUsPlayer(self, ctx, members):
    for member in members:
      info(ctx, "amf remove {}".format(member.name))
      if self.roleAmongUs in member.roles:
        info(ctx, "Removing {} from the {} players".format(member.name, self.roleAmongUs.name))
        await member.remove_roles(\
          self.roleAmongUs,\
          reason="{} requested to no longer receive pings regarding Among Us games".format(member.name))
        await self.channelBot.send(content="{} is now Among The Hidden.".format(member.mention))
      else:
        await warn(ctx, "{} isn't among the {} players".format(member.name, self.roleAmongUs.name))

  async def notifyAmongUsGame(self, ctx, channel, code):
    match = re.compile(r'^([A-Za-z]{6})$').search(code)
    if bool(match) == False:
      await err(ctx, "Bad room code `{}`. Must be six letters.".format(code))
    code = code.upper()
    info(ctx, "Notifying {} of Among Us game code {} in channel {}".format(self.roleAmongUs.name, code, channel.name))
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
