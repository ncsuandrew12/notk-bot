# Standard
import inspect
import re

# Modules
import discord

# Local
import Error
import Logging
import LoggingDiscord as dlog

from Config import cfg
from DiscordFacsimilies import DiscordContextStub
from Logging import logger as log

class GuildBot:
  def __init__(self, bot, guild, loop, database):
    self.bot = bot
    self.database = database
    self.guild = guild
    self.loop = loop
    self.channelAmongUsCodes = None
    self.channelBot = None
    self.channelLog = None
    self.roleAmongUs = None

  # TODO return map
  def GetBotChannels(self):
    channels = []
    for channel in self.guild.channels:
      if channel.name in [ cfg.cAmongUsCodesChannelName, cfg.cBotChannelName, cfg.cLogChannelName ]:
        channels.append(channel)
    return channels

  # TODO return map
  def GetBotRoles(self):
    roles = []
    for role in self.guild.roles:
      if role.name.lower() in [ cfg.cAmongUsRoleName.lower() ]:
        roles.append(role)
    return roles

  async def Startup(self):
    self.database.StartBot(self.guild.id)

    logExtra = self.GetLogExtra()

    self.logHandler = Logging.DiscordLogChannelHandler(self)
    self.logHandler.setFormatter(Logging.discordLogChannelFormatter)
    log.addHandler(self.logHandler)

    log.debug("Starting %s (before channel located)", __name__, extra=logExtra)

    # TODO Instead of simply checking names, keep a persistent log of things created by the bot?

    # Check for existing channels
    self.botChannels = self.GetBotChannels()
    for channel in self.botChannels:
      if channel.name == cfg.cAmongUsCodesChannelName:
        self.channelAmongUsCodes = channel
      elif channel.name == cfg.cBotChannelName:
        self.channelBot = channel
      elif channel.name == cfg.cLogChannelName:
        self.channelLog = channel
      else:
        continue
      log.debug("Found: %s", channel.mention, extra=logExtra)

    # Check for existing roles
    self.botRoles = self.GetBotRoles()
    for role in self.botRoles:
      if role.name.lower() == cfg.cAmongUsRoleName.lower():
        self.roleAmongUs = role
      else:
        continue
      log.info('Found: `@%s`', role.name, extra=logExtra)

  def GetLogExtra(self):
    return Logging.LogExtra(DiscordContextStub(self.guild, self.bot.user))

  async def Setup(self):
    roleMod = None

    logExtra = self.GetLogExtra()

    log.info("Starting %s", __name__, extra=logExtra)

    # Get version information from file
    versionStr=""
    versionPath = 'VERSION'
    versionFile = open(versionPath, 'r')
    try:
      versionStr = versionFile.readline().strip()
      if len(versionStr) < 3: # M.m
        Err(logExtra, "Could not read version information from file: '{}'".format(versionPath))
    except:
      log.error("Could not read version information from file: '%s'", versionPath, extra=logExtra)
      raise
    finally:
      versionFile.close()
    if cfg.cTestMode:
      versionMajor=int(re.sub(r"([0-9]+)\.[0-9]+", r"\1", versionStr))
      versionMinor=int(re.sub(r"[0-9]+\.([0-9]+)", r"\1", versionStr))
      versionMinor+=1
      versionStr="{}.{}".format(versionMajor, versionMinor)
    log.info("Version: %s", versionStr, extra=logExtra)

    # Get release notes information from file
    releaseNotes = {}
    releaseNotesPath = 'RELEASE_NOTES'
    releaseNotesFile = open(releaseNotesPath, 'r')
    try:
      rawLine = "none"
      while rawLine:
        rawLine = releaseNotesFile.readline()
        line = rawLine.strip()
        match = re.search(r'^([A-Z ]+)$', line)
        if match:
          releaseNotesSection = match.group(1)
          releaseNotes[releaseNotesSection] = ""
        elif rawLine:
          releaseNotes[releaseNotesSection] += rawLine
    except Exception as e:
      log.error("Could not read release notes from file: '%s'", releaseNotesPath, extra=logExtra)
      raise
    finally:
      releaseNotesFile.close()
    for key in releaseNotes:
      releaseNotes[releaseNotesSection].strip()
    log.info("Release Notes: %s", releaseNotes, extra=logExtra)

    # TODO delete
    # if bool(self.channelBot):
    #   await self.channelBot.delete(reason="pre-setup")
    #   guildBot.channelBot = None

    # Create the bot log channel if necessary
    if not self.channelLog:
      log.debug('Creating %s log channel: `#%s`', self.bot.user.mention, cfg.cLogChannelName, extra=logExtra)
      overwrites = {
        self.guild.default_role: discord.PermissionOverwrite(send_messages=False),
        self.guild.me: discord.PermissionOverwrite(
          manage_messages=True,
          read_messages=True,
          send_messages=True)
      }
      self.channelLog = await self.guild.create_text_channel(
        name=cfg.cLogChannelName,
        overwrites=overwrites,
        topic="NOTK Bot Log",
        reason="Need a place to put logs")
      self.botChannels.append(self.channelLog)
      dlog.Info(logExtra, 'Created %s log channel: `#%s`', self.bot.user.mention, self.channelLog.mention)

    # TODO delete
    # for role in logExtra.discordContext.guild.roles:
    #   if role.name == cfg.cAmongUsRoleName:
    #     await role.delete(reason="cleanup")

    # Check for existing roles
    roleNames = []
    for role in self.guild.roles:
      roleNames.append(role.name)
      if (role.name.lower() == cfg.cRoleModPrefix.lower()) | \
         ((not roleMod) &
          (role.name.lower().startswith(cfg.cRoleModPrefix.lower()) |
           (cfg.cRoleModSubstring.lower() in role.name.lower()))):
        roleMod = role
      else:
        continue
      log.info('Found: `@%s`', role.name, extra=logExtra)
    log.info('Roles: `%s`', '`, `@'.join(roleNames), extra=logExtra)

    if not roleMod:
      log.warning("%s role not found.", cfg.cRoleModPrefix, extra=logExtra)

    # Create the role
    if not self.roleAmongUs:
      dlog.Info(logExtra, 'Creating `@%s`', cfg.cAmongUsRoleName)
      self.roleAmongUs = await self.guild.create_role(
        name=cfg.cAmongUsRoleName,
        mentionable=True,
        hoist=False,
        reason="Allow users to easily ping everyone interested in playing Among Us.")
        #colour=Colour.gold,
      self.botRoles.append(self.roleAmongUs)

    # Check the existing pinned messages and parse data from them
    amongUsRoleMessage = None
    releaseNotesMessage = None
    if self.channelBot:
      # FIXME Parse all history until we find the instructional message
      for message in await self.channelBot.history(limit=None, oldest_first=True).flatten():
        if message.author.id == self.bot.user.id:
          # log.info('Found message in %s: [%s]',
          #   self.channelBot.mention,
          #   message.content,
          #   extra=logExtra)
          if cfg.cInstructionalLine in message.content.partition('\n')[0]:
            amongUsRoleMessage = message
            log.info('Found %s instructional message in %s: %s',
              message.author.mention,
              self.channelBot.mention,
              message.jump_url,
              extra=logExtra)
          elif message.content.startswith(cfg.cReleaseNotesHeader):
            releaseNotesMessage = message
            log.info('Found %s release notes message in %s: %s',
              message.author.mention,
              self.channelBot.mention,
              message.jump_url,
              extra=logExtra)

    # TODO delete this after notk is cleaned up.
    for channel in self.guild.channels:
      for message in await channel.history(limit=None, oldest_first=True).flatten():
        if (message.content.startswith(cfg.cCommandBase)):
          await message.delete()

    # TODO delete this after notk is cleaned up
    for channel in self.botChannels:
      for message in await channel.history(limit=None, oldest_first=True).flatten():
        if (message.author.id != self.bot.user.id):
          await message.delete()

    # Create main bot channel
    if not self.channelBot:
      log.debug('Creating %s channel: `#%s`', self.bot.user.mention, cfg.cBotChannelName, extra=logExtra)
      overwrites = {
        self.guild.default_role: discord.PermissionOverwrite(send_messages=False),
        self.guild.me: discord.PermissionOverwrite(
          manage_messages=True,
          read_messages=True,
          send_messages=True)
      }
      self.channelBot = await self.guild.create_text_channel(
        name=cfg.cBotChannelName,
        overwrites=overwrites,
        topic="NOTK Bot",
        reason="Need a place to put our instructional message and send join/leave notifications")
      self.botChannels.append(self.channelBot)
      dlog.Info(logExtra, 'Created %s channel: %s', self.bot.user.mention, self.channelBot.mention)

      await self.channelBot.send(
        content="{}{} has added support for the Among Us player group via the {} role.".format(
          roleMod.mention + ", " if roleMod else "",
          self.bot.user.mention,
          self.roleAmongUs.mention))

    # TODO Delete after notk has been updated
    if self.channelAmongUsCodes:
      # TODO grant mods the ability to manage and send messages
      overwrite = discord.PermissionOverwrite()
      overwrite.view_channel=True
      overwrite.manage_messages=True
      await self.channelAmongUsCodes.set_permissions(self.guild.me, overwrite=overwrite)
      overwrite = discord.PermissionOverwrite()
      overwrite.view_channel=True
      await self.channelAmongUsCodes.set_permissions(self.roleAmongUs, overwrite=overwrite)
      overwrite = discord.PermissionOverwrite()
      overwrite.view_channel=False
      await self.channelAmongUsCodes.set_permissions(self.guild.default_role, overwrite=overwrite)

    # Create Among Us codes channel
    if not self.channelAmongUsCodes:
      log.debug('Creating %s channel: `#%s`', self.bot.user.mention, cfg.cAmongUsCodesChannelName, extra=logExtra)
      # TODO grant mods the ability to manage and send messages
      overwrites = {
        self.guild.default_role: discord.PermissionOverwrite(
          view_channel=False),
        self.roleAmongUs: discord.PermissionOverwrite(
          view_channel=True),
        self.guild.me: discord.PermissionOverwrite(
          view_channel=True,
          manage_messages=True)
      }
      self.channelAmongUsCodes = await self.guild.create_text_channel(
        name=cfg.cAmongUsCodesChannelName,
        overwrites=overwrites,
        topic="Among Us Game Code Notifications",
        reason="Need a place to put our Among Us game code notifications so as not to pollute actual chat channels.")
      self.botChannels.append(self.channelAmongUsCodes)
      dlog.Info(logExtra, 'Created %s channel: %s', self.bot.user.mention, self.channelAmongUsCodes.mention)

    releaseNotesLatestSection = ""
    if releaseNotes[cfg.cExternalChanges]:
      releaseNotesLatestSection = "Version {}:\n{}".format(
        versionStr,
        releaseNotes[cfg.cExternalChanges])

    # Handle release notes pinned message
    oldVersionStr = None
    releaseNotesSections = []
    index = -1
    if releaseNotesMessage:
      for line in releaseNotesMessage.content.splitlines():
        match = re.search(r'^Version ([0-9]+\.[0-9]+):$', line)
        if match:
          if not oldVersionStr:
            oldVersionStr = match.group(1)
          releaseNotesSections.append(line + "\n")
          index += 1
        elif index >= 0:
          releaseNotesSections[index] += line + "\n"
    if not oldVersionStr:
      oldVersionStr = "0.0"

    if len(releaseNotesSections):
      if versionStr == oldVersionStr:
        releaseNotesSections[0] = releaseNotesLatestSection
      else:
        releaseNotesSections.insert(0, releaseNotesLatestSection)
    else:
      releaseNotesSections = [ releaseNotesLatestSection ]
    releaseNotesMessageText = "{}\n\n{}".format(cfg.cReleaseNotesHeader, "".join(releaseNotesSections))

    if not releaseNotesMessage:
      dlog.Info(logExtra, 'Sending `@%s` release notes message', cfg.cAmongUsRoleName)
      releaseNotesMessage = await self.channelBot.send(content=releaseNotesMessageText)
    elif releaseNotesMessage.content == releaseNotesMessageText:
      # This should indicate that this is a simple restart.
      log.info('Found up-to-date %s release notes message in %s: %s',
        releaseNotesMessage.author.mention,
        self.channelBot.mention,
        releaseNotesMessage.jump_url,
        extra=logExtra)
    else:
      if (versionStr != oldVersionStr):
        dlog.Info(logExtra, 'Updating existing %s release notes message in %s: %s',
          releaseNotesMessage.author.mention,
          self.channelBot.mention,
          releaseNotesMessage.jump_url)
      await releaseNotesMessage.edit(content=releaseNotesMessageText)
      if (versionStr != oldVersionStr):
        await self.channelBot.send(content="{}{} has been updated!\n{}".format(
          roleMod.mention + ", " if roleMod else "",
          self.bot.user.mention,
          releaseNotesSections[0]))
    if releaseNotesMessage.pinned:
      log.info('`@%s` release notes message already pinned.', cfg.cAmongUsRoleName, extra=logExtra)
    else:
      dlog.Info(logExtra, 'Pinning `@%s` release notes message', cfg.cAmongUsRoleName)
      await releaseNotesMessage.pin(
        reason="The `@{}` release notes message will get buried if it isn't pinned".format(cfg.cBotName))

    # Handle instructional pinned message
    amongUsRoleMessageText = \
    """{}
Type `{}` in any public channel to be notified about NOTK Among Us game sessions.
Type `{}` in any public channel if you no longer want to be notified.
{} New game notifications appear in the {} channel.
Tag the `{}` role to ping all Among Us players like so: {}
I recommend muting the {} channel; it is only for logging purposes and will be very noisy.
You might also want to mute the {} channel, but it will give you helpful messages if you make mistakes using these commands.""".format(
      cfg.cInstructionalLine,
      cfg.cAmongUsJoinRequestMessageText,
      cfg.cAmongUsLeaveRequestMessageText,
      cfg.cAmongUsSendGameNotificationText,
      self.channelAmongUsCodes.mention,
      cfg.cAmongUsRoleName,
      self.roleAmongUs.mention,
      self.channelLog.mention,
      self.channelBot.mention)
    if not amongUsRoleMessage:
      dlog.Info(logExtra, 'Sending `@%s` instructional message', cfg.cAmongUsRoleName)
      amongUsRoleMessage = await self.channelBot.send(content=amongUsRoleMessageText)
    elif amongUsRoleMessage.content == amongUsRoleMessageText:
      # This should indicate that this is a simple restart.
      log.info(
        'Found up-to-date %s instructional message in %s: %s',
        amongUsRoleMessage.author.mention,
        self.channelBot.mention,
        amongUsRoleMessage.jump_url,
        extra=logExtra)
    else:
      await amongUsRoleMessage.delete()
      dlog.Info(logExtra, 'Sending `@%s` instructional message', cfg.cAmongUsRoleName)
      amongUsRoleMessage = await self.channelBot.send(content=amongUsRoleMessageText)
      # dlog.Info(
      #   logExtra,
      #   'Updating existing %s instructional message in %s: %s',
      #   amongUsRoleMessage.author.mention,
      #   self.channelBot.mention,
      #   amongUsRoleMessage.jump_url)
      # await amongUsRoleMessage.edit(content=amongUsRoleMessageText)
    if amongUsRoleMessage.pinned:
      log.info('`@%s` instructional message already pinned.', cfg.cAmongUsRoleName, extra=logExtra)
    else:
      dlog.Info(logExtra, 'Pinning `@%s` instructional message', cfg.cAmongUsRoleName)
      await amongUsRoleMessage.pin(
        reason="The `@{}` instructional message needs to be very visible to be useful".format(cfg.cBotName))

    self.database.BotStarted(self.guild.id)

    dlog.Info(logExtra, "%s started.", __name__)

  def Shutdown(self):
    log.info("Shutting down.", extra=self.GetLogExtra())
    log.removeHandler(self.logHandler)
    self.logHandler.flush()
    self.logHandler.close()
    return self.database.ShutdownBot(self.guild.id)

  async def Command(self, logExtra, cmd, *args):
    if bool(logExtra.discordContext.message):
      await logExtra.discordContext.message.delete()

    log.debug("Processing command: `%s %s`", cmd, " ".join(args), extra=logExtra)

    # Parse the arguments as tagged members
    members = []
    memberNames = []
    resolved = []
    if cmd in [ cfg.cCommandJoin, cfg.cCommandLeave]:
      if len(args) > 0:
        userIDs = {}
        for arg in args:
          if arg.startswith('<@') & arg.endswith('>'):
            userID = arg[2:-1]
            while userID.startswith('!') | userID.startswith('&'):
              userID = userID[1:len(userID)]
            userIDs[userID] = arg
        for userID in userIDs:
          try:
            member = await logExtra.discordContext.guild.fetch_member(userID)
          except Exception as e:
            log.warning("userID `%s`: %s", userID, str(e), extra=logExtra)
          except:
            log.warning("userID `%s`: %s", userID, str(sys.exc_info()[0]), extra=logExtra)
          else:
            if member.name not in memberNames:
              resolved.append(userIDs[userID])
              members.append(member)
              memberNames.append(member.name)
      else:
        member = await logExtra.discordContext.guild.fetch_member(logExtra.discordContext.author.id)
        members = [member]
        memberNames = [member.name]
      missing = set(args) - set(resolved)
      if (len(missing) > 0):
        dlog.Warn(logExtra, "Could not find members: `%s`!", "`, `".join(missing))

    if cmd == cfg.cCommandJoin:
      await self.AddAmongUsPlayer(logExtra, members)
    elif cmd == cfg.cCommandLeave:
      await self.RemoveAmongUsPlayer(logExtra, members)
    elif cmd == cfg.cCommandNewGame:
      await self.NotifyAmongUsGame(logExtra, args[0])
    else:
      Error.DErr(logExtra, "Invalid command `%s`.", cmd)

  async def AddAmongUsPlayer(self, logExtra, members):
    alreadyMemberNames = []
    for member in members:
      if self.roleAmongUs in member.roles:
        alreadyMemberNames.append(member.name)
      else:
        dlog.Info(logExtra, "Adding `@%s` to the `@%s` players", member.name, self.roleAmongUs.name)
        await member.add_roles(
          self.roleAmongUs,
          reason="{} requested for {} to be pinged regarding Among Us games".format(
            logExtra.discordContext.author.name,
            member.name))
        await self.channelBot.send(
          content="Hey `@{}` players! {} is now among the Among Us players!".format(
            self.roleAmongUs.name,
            member.mention))
        if not member.bot:
          await member.send(
            content="You have been added to `{}`'s Among Us players. Type `{}` in any public channel in `{}` to leave the Among Us players.".format(
                logExtra.discordContext.guild.name,
                cfg.cAmongUsLeaveRequestMessageText,
                logExtra.discordContext.guild.name))
    if (len(alreadyMemberNames) > 0):
      dlog.Warn(logExtra, "Members already have `@%s` role: `@%s`!", self.roleAmongUs.name, "`, `@".join(alreadyMemberNames))

  async def RemoveAmongUsPlayer(self, logExtra, members):
    missingMemberNames = []
    for member in members:
      if self.roleAmongUs in member.roles:
        dlog.Info(logExtra, "Removing `@%s` from the `@%s` players", member.name, self.roleAmongUs.name)
        await member.remove_roles(
          self.roleAmongUs,
          reason="{} requested for {} to no longer receive pings regarding Among Us games".format(
            logExtra.discordContext.author.name,
            member.name))
        await self.channelBot.send(content="{} is now Among The Hidden.".format(member.mention))
        if not member.bot:
          await member.send(content="You have been remove from `{}`'s Among Us players.".format(ctx.guild.name))
      else:
        missingMemberNames.append(member.name)
    if (len(missingMemberNames) > 0):
      dlog.Warn(
        logExtra,
        "`@%s` isn't among the `@%s` players",
        "`, `@".join(missingMemberNames),
        self.roleAmongUs.name)

  async def NotifyAmongUsGame(self, logExtra, code):
    match = re.compile(r'^([A-Za-z]{6})$').search(code)
    if not match:
      Error.ErrMinor(logExtra, "Bad room code `%s`. Must be six letters.", code)
    code = code.upper()
    dlog.Info(
      logExtra,
      "Notifying `@%s` of Among Us game code `%s` in `#%s`",
      self.roleAmongUs.name,
      code, self.channelAmongUsCodes.name)
    await self.channelAmongUsCodes.send(
      content="Attention {}! New game code: `{}`. Type `{}` if you no longer want to receive these notifications. {}".format(
        self.roleAmongUs.mention,
        code,
        cfg.cAmongUsLeaveRequestMessageText,
        cfg.cAmongUsSendGameNotificationText))
