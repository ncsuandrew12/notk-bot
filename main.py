import discord
import os
import re

from discord.ext import commands

cAmongUsCodesChannelName = "among-us-codes"
cAmongUsRoleName = "among-us"
cAmongUsSendGameNotificationText = ""
cCommandRoot = "au"
cCommandJoin = "join"
cCommandLeave = "leave"
cCommandNewGame = "newgame"
cBotChannelName = "notk-bot"
cModRolePrefix = "mod"

kAmongUsCodesChannel = False
kAmongUsRole = False
kBotChannel = False
kModRole = False

bot = commands.Bot(command_prefix='$')

cCommandBase = "{}{}".format(bot.command_prefix, cCommandRoot)

cAmongUsJoinRequestMessageText = "{} {}".format(cCommandBase, cCommandJoin)
cAmongUsLeaveRequestMessageText = "{} {}".format(cCommandBase, cCommandLeave)
cAmongUsSendGameNotificationText = "Type `{} {} <room-code>` to send a new game notification.".format(cCommandBase, cCommandNewGame)

@bot.command()
async def au(ctx, cmd, *args):
  await setup(ctx)
  if cmd == cCommandJoin:
    await addAmongUsPlayer(ctx, ctx.author.id)
  elif cmd == cCommandLeave:
    await removeAmongUsPlayer(ctx, ctx.author.id)
  elif cmd == cCommandNewGame:
    match = re.compile(r'^([A-Za-z]{6})$').search(args[0])
    if bool(match):
      await notifyAmongUsGame(ctx.message.channel, match.group(1).upper())
    else:
      print("ERROR: Bad room code given by {}.{}: `{}`. Must be six letters.".format(\
        ctx.guild.name,\
        ctx.author.name,\
        args[0]))
      await ctx.author.send("ERROR: Bad room code `{}`. Must be six letters.".format(args[0]))

async def setup(ctx):
  global kAmongUsCodesChannel
  global kAmongUsRole
  global kBotChannel
  global kModRole

  if bool(kBotChannel):
    return

  print('Running setup on {}'.format(ctx.guild.name))

  for role in ctx.guild.roles:
    if role.name.startswith(cModRolePrefix):
      kModRole = role
    elif role.name == cAmongUsRoleName:
      kAmongUsRole = role
    else:
      continue
    print('Found role: {}'.format(role.name))
  
  if kModRole == False:
    print("Warning: {} role not found.".format(cModRolePrefix))

  if kAmongUsRole == False:
    print('Creating {} role'.format(cAmongUsRoleName))
    await ctx.guild.create_role(\
      name=cAmongUsRoleName,\
      mentionable=True,\
      hoist=False,\
      reason="Allow users to easily ping everyone interested in playing Among Us.")
      #colour=Colour.gold,\

  amongUsRoleMessageText = \
  """⚠ notk-bot Instructions ⚠
Type `{}` in any channel to be notified about NOTK Among Us game sessions.
Type `{}` in any channel if you no longer want to be notified.
{}
Tag the `{}` role to ping all Among Us players like so: {}
""".format(\
    cAmongUsJoinRequestMessageText,\
    cAmongUsLeaveRequestMessageText,\
    cAmongUsSendGameNotificationText,\
    cAmongUsRoleName,\
    kAmongUsRole.mention)

  for channel in ctx.guild.channels:
    if channel.name == cBotChannelName:
      kBotChannel = channel
    elif channel.name == cAmongUsCodesChannelName:
      kAmongUsCodesChannel = channel
    else:
      continue
    print('Found channel: {}'.format(channel.name))

  # TODO delete
#  if kBotChannel != False:
#    await kBotChannel.delete(reason="pre-setup")
#    kBotChannel = False

  amongUsRoleMessage = 0
  if kBotChannel != False:
    for message in await kBotChannel.history(limit=200).flatten():
      if message.content == amongUsRoleMessageText:
        print('Found {} instructional message in #{}'.format(ctx.user.name, kBotChannel.name))
        amongUsRoleMessage = message
      elif message.content.startswith("⚠ notk-bot Instructions ⚠") & (message.author.id == bot.user.id):
        print('Deleting old message by {} in #{}'.format(message.author.name, kBotChannel.name))
        await message.delete()
      #else:
        #print("Found message: {}".format(message.content))
  else:
    print('Creating bot channel: {}'.format(cBotChannelName))
    overwrites = {
      ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
      ctx.guild.me: discord.PermissionOverwrite(\
        manage_messages=True,\
        read_messages=True,\
        send_messages=True)
    }
    kBotChannel = await ctx.guild.create_text_channel(\
      name=cBotChannelName,\
      overwrites=overwrites,\
      topic="NOTK Bot",\
      reason="Need a place to put our message for users to react to")

    await kBotChannel.send(content="{}{}{} has added support for the Among Us player group via the {} role.".format(\
      kModRole.mention if kModRole != False else "",\
      ", " if kModRole != False else "",\
      bot.user.mention,\
      kAmongUsRole.mention))
  
  if amongUsRoleMessage == False:
    print('Sending {} role message'.format(cAmongUsRoleName))
    amongUsRoleMessage = await kBotChannel.send(content=amongUsRoleMessageText)
  
  if amongUsRoleMessage.pinned == True:
    print('{} role message already pinned.'.format(cAmongUsRoleName))
  else:
    print('Pinning {} role message'.format(cAmongUsRoleName))
    await amongUsRoleMessage.pin(reason="The {} instructional message needs to be very visible to be useful".format(cBotChannelName))

async def addAmongUsPlayer(ctx, userid):
  member = await ctx.guild.fetch_member(userid)
  hasRole = False
  for role in member.roles:
    if role == kAmongUsRole:
      print("@{} is already among the {} players".format(member.name, role.name))
      await ctx.author.send("You are already among the {} players.".format(role.name))
      hasRole = True
  if hasRole == False:
    print("Adding @{} to the {} players".format(member.name, kAmongUsRole.name))
    await member.add_roles(\
      kAmongUsRole,\
      reason="{} requested to be pinged regarding Among Us games".format(member.name))
    await kBotChannel.send(\
      content="{} is now among the Among Us players! Type `{}` to leave the Among Us players.".format(\
        member.mention,\
        cAmongUsLeaveRequestMessageText))

async def removeAmongUsPlayer(ctx, userid):
  member = await ctx.guild.fetch_member(userid)
  for role in member.roles:
    if role == kAmongUsRole:
      print("Removing @{} from the {} players".format(kAmongUsRole.name, member.name))
      await member.remove_roles(\
        kAmongUsRole,\
        reason="@{} requested to no longer receive pings regarding Among Us games".format(member.name))
      return
  await ctx.author.send("You aren't among the {} players.".format(kAmongUsRole.name))

async def notifyAmongUsGame(channel, code):
  print("Notifying @{} of Among Us game code {} in channel {}".format(kAmongUsRole.name, code, channel.name))
  await channel.send(\
    content="Attention {}! New game code: `{}`. Type `{}` if you no longer want receive these notifications. {}".format(\
      kAmongUsRole.mention,\
      code,\
      cAmongUsLeaveRequestMessageText,\
      cAmongUsSendGameNotificationText))
#  codeSpelled = re.sub(r"([A-Z])", r"\1 ", code)
#  await channel.send(content="New game code: `{}`.".format(codeSpelled),\
#                     tts=True)

tokenFile = open('discord.token', 'r')

try:
  token = tokenFile.readline()
finally:
  tokenFile.close()

bot.run(token)
