# Modules
# import discord
# import inspect
# import json
# import os
import re
# import sys

# from discord.ext import commands

# notk-bot
import Error
import Logging as log
import LoggingDiscord as dlog

from Config import cfg
from DiscordFacsimilies import AuthorStubbed
from DiscordFacsimilies import ContextStubbed

class GuildBot:
  def __init__(self):
    self.channelBot = None
    self.channelLog = None
    self.roleAmongUs = None

  async def setup(self, user, guild):
    self.user = user

    roleMod = None

    ctx = ContextStubbed(guild, AuthorStubbed(guild.name))

    dlog.debug(ctx, "Starting bot (before channel located)")

    for channel in guild.channels:
      if channel.name == cfg.cBotChannelName:
        self.channelBot = channel
      elif channel.name == cfg.cLogChannelName:
        self.channelLog = channel
      else:
        continue
      dlog.debug(ctx, 'Found: `#{}`'.format(channel.name))

    # TODO delete
    # if bool(self.channelBot):
    #   await self.channelBot.delete(reason="pre-setup")
    #   guildBot.channelBot = None

    if bool(self.channelLog) == False:
      dlog.debug(ctx, 'Creating bot log: `#{}`'.format(cfg.cLogChannelName))
      overwrites = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False),
        guild.me: discord.PermissionOverwrite(\
          manage_messages=True,\
          read_messages=True,\
          send_messages=True)
      }
      self.channelLog = await guild.create_text_channel(\
        name=cfg.cLogChannelName,\
        overwrites=overwrites,\
        topic="NOTK Bot Log",\
        reason="Need a place to put logs")

    await self.info(ctx, "Starting bot")

    # TODO delete
    # for role in ctx.guild.roles:
    #   if role.name == cfg.cAmongUsRoleName:
    #     await role.delete(reason="cleanup")

    for role in guild.roles:
      if bool(roleMod) & \
         (role.name.lower().startswith(cfg.cRoleModPrefix.lower()) |\
          bool(cfg.cRoleModSubstring.lower() in role.name.lower())):
        roleMod = role
      elif role.name == cfg.cAmongUsRoleName:
        self.roleAmongUs = role
      else:
        continue
      await self.info(ctx, 'Found: `@{}`'.format(role.name))

    # TODO Enable, but avoid sending messages to just whoever sent the command
    # if bool(roleMod) == False:
    #   await dlog.warn(self, "{} role not found.".format(cfg.cRoleModPrefix))

    if bool(self.roleAmongUs) == False:
      await self.info(ctx, 'Creating `@{}`'.format(cfg.cAmongUsRoleName))
      self.roleAmongUs = await guild.create_role(\
        name=cfg.cAmongUsRoleName,\
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
      cfg.cAmongUsJoinRequestMessageText,\
      cfg.cAmongUsLeaveRequestMessageText,\
      cfg.cAmongUsSendGameNotificationText,\
      cfg.cAmongUsRoleName,\
      self.roleAmongUs.mention,
      self.channelLog.mention)

    amongUsRoleMessage = None
    if bool(self.channelBot):
      for message in await self.channelBot.history(limit=200).flatten():
        if message.author.id == self.user.id:
          if message.content == amongUsRoleMessageText:
            await self.info(ctx, 'Found `{}` instructional message in `#{}`'.format(message.author.name, self.channelBot.name))
            amongUsRoleMessage = message
          # elif message.content.startswith("⚠ notk-bot Instructions ⚠"):
            # await self.info(ctx, 'Deleting old message by `@{}` in `#{}`'.format(message.author.name, self.channelBot.name))
            # await message.delete()
          #else:
            #dlog.info(ctx, guildBot, "Found message: {}".format(message.content))
        #else:
          #dlog.info(ctx, guildBot, "Found message: {}".format(message.content))
    else:
      await self.info(ctx, 'Creating bot channel: `#{}`'.format(cfg.cBotChannelName))
      overwrites = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False),
        guild.me: discord.PermissionOverwrite(\
          manage_messages=True,\
          read_messages=True,\
          send_messages=True)
      }
      self.channelBot = await guild.create_text_channel(\
        name=cfg.cBotChannelName,\
        overwrites=overwrites,\
        topic="NOTK Bot",\
        reason="Need a place to put our instructional message and send join/leave notifications")

      await self.channelBot.send(content="{}{}{} has added support for the Among Us player group via the `@{}` role.".format(\
        roleMod.mention if bool(roleMod) else "",\
        ", " if bool(roleMod) else "",\
        self.user.mention,\
        self.roleAmongUs.mention))

    if amongUsRoleMessage == None:
      await self.info(ctx, 'Sending `{}` instructional message'.format(cfg.cAmongUsRoleName))
      amongUsRoleMessage = await self.channelBot.send(content=amongUsRoleMessageText)
    
    if amongUsRoleMessage.pinned == True:
      await self.info(ctx, '`{}` instructional message already pinned.'.format(cfg.cAmongUsRoleName))
    else:
      await self.info(ctx, 'Pinning {} instructional message'.format(cfg.cAmongUsRoleName))
      await amongUsRoleMessage.pin(reason="The `{}` instructional message needs to be very visible to be useful".format(cfg.kBotName))

    await self.info(ctx, "Bot started.")

  async def addAmongUsPlayer(self, ctx, members):
    alreadyMemberNames = []
    for member in members:
      if self.roleAmongUs in member.roles:
        alreadyMemberNames.append(member.name)
      else:
        await self.info(ctx, "Adding `@{}` to the `@{}` players".format(member.name, self.roleAmongUs.name))
        await member.add_roles(\
          self.roleAmongUs,\
          reason="{} requested for {} to be pinged regarding Among Us games".format(\
            ctx.author.name,\
            member.name))
        await self.channelBot.send(\
          content="Hey {} players! {} is now among the Among Us players!".format(\
            self.roleAmongUs.mention,\
            member.mention))
        if not member.bot:
          await member.send(\
            content="You have been added to `{}`'s Among Us players. Type `{}` in any public channel in `{}` to leave the Among Us players.".format(\
              ctx.guild.name,\
              cfg.cAmongUsLeaveRequestMessageText,\
              ctx.guild.name))
    if (len(alreadyMemberNames) > 0):
      await dlog.warn(self, ctx, "`@{}` {} already among the `@{}` players".format(\
        "`, `@".join(alreadyMemberNames),\
        "is" if len(alreadyMemberNames) == 1 else "are",\
        self.roleAmongUs.name))

  async def removeAmongUsPlayer(self, ctx, members):
    missingMemberNames = []
    for member in members:
      if self.roleAmongUs in member.roles:
        await self.info(ctx, "Removing `@{}` from the `@{}` players".format(member.name, self.roleAmongUs.name))
        await member.remove_roles(\
          self.roleAmongUs,\
          reason="{} requested for {} to no longer receive pings regarding Among Us games".format(\
            ctx.author.name,\
            member.name))
        await self.channelBot.send(content="{} is now Among The Hidden.".format(member.mention))
        if not member.bot:
          await member.send(content="You have been remove from `{}`'s Among Us players.".format(ctx.guild.name))
      else:
        missingMemberNames.append(member.name)
    if (len(missingMemberNames) > 0):
      await self.warn(ctx, "`@{}` isn't among the `@{}` players".format(\
        "`, `@".join(missingMemberNames),\
        self.roleAmongUs.name))

  async def notifyAmongUsGame(self, ctx, channel, code):
    match = re.compile(r'^([A-Za-z]{6})$').search(code)
    if bool(match) == False:
      await self.errMinor(ctx, "Bad room code `{}`. Must be six letters.".format(code))
    code = code.upper()
    await self.info(ctx, "Notifying `@{}` of Among Us game code `{}` in `#{}`".format(self.roleAmongUs.name, code, channel.name))
    await channel.send(\
      content="Attention {}! New game code: `{}`. Type `{}` if you no longer want receive these notifications. {}".format(\
        self.roleAmongUs.mention,\
        code,\
        cfg.cAmongUsLeaveRequestMessageText,\
        cfg.cAmongUsSendGameNotificationText))
  #  codeSpelled = re.sub(r"([A-Z])", r"\1 ", code)
  #  await channel.send(content="New game code: `{}`.".format(codeSpelled),\
  #                     tts=True)

  async def info(self, ctx, msg):
    await dlog.info(self, ctx, msg)

  async def warn(self, ctx, msg):
    await dlog.warn(self, ctx, msg)

  async def err(self, ctx, msg):
    await Error.err(self, ctx, msg)

  async def errMinor(self, ctx, msg):
    await Error.errMinor(self, ctx, msg)

