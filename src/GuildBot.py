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
    self.botRoles = []
    self.database = database
    self.guild = guild
    self.loop = loop
    self.channelAmongUsCodes = None
    self.channelBot = None
    self.channelLog = None
    self.logExtra = None
    self.messageAmongUsRoleInstructions = None
    self.messageReleaseNotes = None
    self.releaseNotes = None
    self.roleAmongUs = None
    self.roleMod = None
    self.versionMajor = None
    self.versionMinor = None
    self.versionStr = None

  # TODO return map
  def GetBotChannels(self):
    channels = []
    for channel in self.guild.channels:
      log.debug('Channel: `@%s`', channel.name, extra=self.logExtra)
      if channel.name in [ cfg.cAmongUsCodesChannelName, cfg.cBotChannelName, cfg.cLogChannelName ]:
        channels.append(channel)
    return channels

  # TODO return map
  def GetBotRoles(self):
    roles = []
    for role in self.guild.roles:
      log.debug('Role: `@%s`', role.name, extra=self.logExtra)
      if role.name.lower() in [ cfg.cAmongUsRoleName.lower() ]:
        roles.append(role)
    return roles

  async def Startup(self):
    self.database.StartBot(self.guild.id)
    self.logExtra = Logging.LogExtra(DiscordContextStub(self.guild, self.bot.user))
    self.logHandler = Logging.DiscordLogChannelHandler(self)
    self.logHandler.setFormatter(Logging.discordLogChannelFormatter)
    log.addHandler(self.logHandler)
    log.debug("Starting %s (before channel located)", __name__, extra=self.logExtra)
    self.botMember = await self.guild.fetch_member(self.bot.user.id)
    self.LoadChannels()
    self.LoadRoles()

  def LoadChannels(self):
    # TODO Instead of simply checking names, keep a persistent log of things created by the bot?
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
      log.debug("Found: %s", channel.mention, extra=self.logExtra)

  def LoadRoles(self):
    # TODO Instead of simply checking names, keep a persistent log of things created by the bot?
    self.botRoles = self.GetBotRoles()
    roleNames = []
    for role in self.guild.roles:
      roleNames.append(role.name)
      if (role.name.lower() == cfg.cRoleModPrefix.lower()) | \
         ((not self.roleMod) &
          (role.name.lower().startswith(cfg.cRoleModPrefix.lower()) |
           (cfg.cRoleModSubstring.lower() in role.name.lower()))):
        self.roleMod = role
      elif role.name.lower() == cfg.cAmongUsRoleName.lower():
        self.roleAmongUs = role
      else:
        continue
      log.info('Found: `@%s`', role.name, extra=self.logExtra)
    log.info('Roles: `%s`', '`, `@'.join(roleNames), extra=self.logExtra)
    if not self.roleMod:
      log.warning("%s role not found.", cfg.cRoleModPrefix, extra=self.logExtra)

  async def Setup(self):
    log.info("Starting %s", __name__, extra=self.logExtra)
    self.LoadVersion()
    self.LoadReleaseNotes()
    if not self.channelLog:
      await self.CreateLogChannel()
    if not self.roleAmongUs:
      await self.CreateRole()
    await self.LoadReleaseNotesMessage()
    if not self.channelBot:
      await self.CreateBotChannel()
    if not self.channelAmongUsCodes:
      await self.CreateAmongUsCodesChannel()
    await self.UpdateOrSendReleaseNotesMessage()
    await self.SendInstructionalMessageIfNeeded()
    self.database.BotStarted(self.guild.id)
    dlog.Info(self.logExtra, "%s started.", __name__)

  # Version information will be constant across all GuildBots.
  # TODO Move this to GuildBotManager
  def LoadVersion(self):
    self.versionStr=""
    versionPath = 'VERSION'
    versionFile = open(versionPath, 'r')
    try:
      self.versionStr = versionFile.readline().strip()
      if len(self.versionStr) < 3: # M.m
        Error.DErr(self.logExtra, "Could not read version information from file: '{}' ({})".format(versionPath, self.versionStr))
    except:
      log.error("Could not read version information from file: '%s'", versionPath, extra=self.logExtra)
      raise
    finally:
      versionFile.close()
    if cfg.cTestMode:
      self.versionMajor=int(re.sub(r"([0-9]+)\.[0-9]+", r"\1", self.versionStr))
      self.versionMinor=int(re.sub(r"[0-9]+\.([0-9]+)", r"\1", self.versionStr))
      self.versionMinor+=1
      self.versionStr="{}.{}".format(self.versionMajor, self.versionMinor)
    log.info("Version: %s", self.versionStr, extra=self.logExtra)

  def LoadReleaseNotes(self):
    self.releaseNotes = {}
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
          self.releaseNotes[releaseNotesSection] = ""
        elif rawLine:
          self.releaseNotes[releaseNotesSection] += rawLine
    except Exception as e:
      log.error("Could not read release notes from file: '%s'", releaseNotesPath, extra=self.logExtra)
      raise
    finally:
      releaseNotesFile.close()
    for key in self.releaseNotes:
      self.releaseNotes[releaseNotesSection].strip()
    log.info("Release Notes: %s", self.releaseNotes, extra=self.logExtra)
    self.releaseNotesLatestSection = ""
    if self.releaseNotes[cfg.cExternalChanges]:
      self.releaseNotesLatestSection = "Version {}:\n{}".format(
        self.versionStr,
        self.releaseNotes[cfg.cExternalChanges])

  async def CreateLogChannel(self):
    log.debug('Creating %s log channel: `#%s`', self.bot.user.mention, cfg.cLogChannelName, extra=self.logExtra)
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
    dlog.Info(self.logExtra, 'Created %s log channel: `#%s`', self.bot.user.mention, self.channelLog.mention)

  async def CreateRole(self):
    dlog.Info(self.logExtra, 'Creating `@%s`', cfg.cAmongUsRoleName)
    self.roleAmongUs = await self.guild.create_role(
      name=cfg.cAmongUsRoleName,
      mentionable=True,
      hoist=False,
      reason="Allow users to easily ping everyone interested in playing Among Us.")
      #colour=Colour.gold,
    self.botRoles.append(self.roleAmongUs)

  async def LoadReleaseNotesMessage(self):
    # Check the existing release notes messages and parse data from them
    if self.channelBot:
      # FIXME Parse all history until we find the instructional message
      for message in await self.channelBot.history(limit=None, oldest_first=True).flatten():
        if message.author.id == self.bot.user.id:
          # log.info('Found message in %s: [%s]',
          #   self.channelBot.mention,
          #   message.content,
          #   extra=self.logExtra)
          if cfg.cInstructionalLine in message.content.partition('\n')[0]:
            self.messageAmongUsRoleInstructions = message
            log.info('Found %s instructional message in %s: %s',
              message.author.mention,
              self.channelBot.mention,
              message.jump_url,
              extra=self.logExtra)
          elif message.content.startswith(cfg.cReleaseNotesHeader):
            self.messageReleaseNotes = message
            log.info('Found %s release notes message in %s: %s',
              message.author.mention,
              self.channelBot.mention,
              message.jump_url,
              extra=self.logExtra)

  async def CreateBotChannel(self):
    log.debug('Creating %s channel: `#%s`', self.bot.user.mention, cfg.cBotChannelName, extra=self.logExtra)
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
    dlog.Info(self.logExtra, 'Created %s channel: %s', self.bot.user.mention, self.channelBot.mention)
    await self.channelBot.send(
      content="{}{} has added support for the Among Us player group via the {} role.".format(
        self.roleMod.mention + ", " if self.roleMod else "",
        self.bot.user.mention,
        self.roleAmongUs.mention))

  async def CreateAmongUsCodesChannel(self):
    log.debug('Creating %s channel: `#%s`', self.bot.user.mention, cfg.cAmongUsCodesChannelName, extra=self.logExtra)
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
    dlog.Info(self.logExtra, 'Created %s channel: %s', self.bot.user.mention, self.channelAmongUsCodes.mention)

  async def UpdateOrSendReleaseNotesMessage(self):
    oldVersionStr = None
    releaseNotesSections = []
    index = -1
    # Get existing message information
    if self.messageReleaseNotes:
      for line in self.messageReleaseNotes.content.splitlines():
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
    # Add latest release information
    if len(releaseNotesSections):
      if self.versionStr == oldVersionStr:
        releaseNotesSections[0] = self.releaseNotesLatestSection
      else:
        releaseNotesSections.insert(0, self.releaseNotesLatestSection)
    else:
      releaseNotesSections = [ self.releaseNotesLatestSection ]
    releaseNotesMessageText = "{}\n\n{}".format(cfg.cReleaseNotesHeader, "".join(releaseNotesSections))
    # Updated/send the release notes message
    if not self.messageReleaseNotes:
      # Fresh install (or bot channel was re-created)
      dlog.Info(self.logExtra, 'Sending `@%s` release notes message', cfg.cAmongUsRoleName)
      self.messageReleaseNotes = await self.channelBot.send(content=releaseNotesMessageText)
    elif self.messageReleaseNotes.content == releaseNotesMessageText:
      # Non-upgrade restart.
      log.info('Found up-to-date %s release notes message in %s: %s',
        self.messageReleaseNotes.author.mention,
        self.channelBot.mention,
        self.messageReleaseNotes.jump_url,
        extra=self.logExtra)
    else:
      # Release notes need updating
      if (self.versionStr != oldVersionStr):
        dlog.Info(self.logExtra, 'Updating existing %s release notes message in %s: %s',
          self.messageReleaseNotes.author.mention,
          self.channelBot.mention,
          self.messageReleaseNotes.jump_url)
      await self.messageReleaseNotes.edit(content=releaseNotesMessageText)
      # Send a new message just for the latest release info
      if (self.versionStr != oldVersionStr):
        await self.channelBot.send(content="{}{} has been updated!\n{}".format(
          self.roleMod.mention + ", " if self.roleMod else "",
          self.bot.user.mention,
          releaseNotesSections[0]))
    # Ensure that the main release notes message is pinned.
    if self.messageReleaseNotes.pinned:
      log.info('`@%s` release notes message already pinned.', cfg.cAmongUsRoleName, extra=self.logExtra)
    else:
      dlog.Info(self.logExtra, 'Pinning `@%s` release notes message', cfg.cAmongUsRoleName)
      await self.messageReleaseNotes.pin(
        reason="The `@{}` release notes message will get buried if it isn't pinned".format(cfg.cBotName))

  async def SendInstructionalMessageIfNeeded(self):
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
    if not self.messageAmongUsRoleInstructions:
      dlog.Info(self.logExtra, 'Sending `@%s` instructional message', cfg.cAmongUsRoleName)
      self.messageAmongUsRoleInstructions = await self.channelBot.send(content=amongUsRoleMessageText)
    elif self.messageAmongUsRoleInstructions.content == amongUsRoleMessageText:
      # Non-upgrade restart
      log.info(
        'Found up-to-date %s instructional message in %s: %s',
        self.messageAmongUsRoleInstructions.author.mention,
        self.channelBot.mention,
        self.messageAmongUsRoleInstructions.jump_url,
        extra=self.logExtra)
    else:
      dlog.Info(
        self.logExtra,
        'Out-of-date instructional message found.\nOld: %s\nNew: %s',
        amongUsRoleMessageText,
        self.messageAmongUsRoleInstructions.content)
      # Old instructions may be incorrect or misleading. Delete and re-send with the up-to-date instructions.
      await self.messageAmongUsRoleInstructions.delete()
      dlog.Info(self.logExtra, 'Sending `@%s` instructional message', cfg.cAmongUsRoleName)
      self.messageAmongUsRoleInstructions = await self.channelBot.send(content=amongUsRoleMessageText)
    # Ensure that the instructional message is pinned
    if self.messageAmongUsRoleInstructions.pinned:
      log.info('`@%s` instructional message already pinned.', cfg.cAmongUsRoleName, extra=self.logExtra)
    else:
      dlog.Info(self.logExtra, 'Pinning `@%s` instructional message', cfg.cAmongUsRoleName)
      await self.messageAmongUsRoleInstructions.pin(
        reason="The `@{}` instructional message needs to be very visible to be useful".format(cfg.cBotName))

  def Shutdown(self):
    log.info("Shutting down.", extra=self.logExtra)
    log.removeHandler(self.logHandler)
    self.logHandler.flush()
    self.logHandler.close()
    return self.database.ShutdownBot(self.guild.id)

  async def Command(self, cmd, logExtra=None, args=[]):
    if not logExtra:
      logExtra = self.logExtra
    if bool(logExtra.discordContext.message):
      await logExtra.discordContext.message.delete()

    fullCmd = "{} {}{}{}".format(cfg.cCommandBase, cmd, " " if len(args) > 0 else "", " ".join(args));
    log.debug("Processing command: `%s`", fullCmd, extra=logExtra)

    if cmd == cfg.cCommandJoin:
      await self.CommandJoin(logExtra, args)
    elif cmd == cfg.cCommandLeave:
      await self.CommandLeave(logExtra, args)
    elif cmd == "au": # TODO au
      if (len(args) < 1):
        Error.DErr(logExtra, "Missing sub-command")
      subCmd = args[0]
      args.pop(0)
      await self.AUSubCommand(subCmd, logExtra, args)
    else:
      Error.DErr(logExtra, "Invalid command `%s`: `%s`.", cmd, fullCmd)

  async def CommandJoin(self, logExtra, args):
    if (len(args) < 1):
      Error.DErr(logExtra, "Missing role reference parameter")
    roleReference = args[0]
    args.pop(0)
    members = await self.ProcessMemberArgs(logExtra, args)
    log.debug("members=%s", members)
    if roleReference == "au": # TODO au
      await self.AddAmongUsPlayer(logExtra, members)
    else:
      Error.DErr(logExtra, "Bad role reference %s", roleReference)

  async def CommandLeave(self, logExtra, args):
    if (len(args) < 1):
      Error.DErr(logExtra, "Missing role reference parameter")
    roleReference = args[0]
    args.pop(0)
    members = await self.ProcessMemberArgs(logExtra, args)
    if roleReference == "au": # TODO au
      await self.RemoveAmongUsPlayer(logExtra, members)
    else:
      Error.DErr(logExtra, "Bad role reference %s", roleReference)

  async def ProcessMemberArgs(self, logExtra, args):
    members = []
    memberNames = []
    resolved = []
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
    return members

  async def AUSubCommand(self, cmd, logExtra, args):
    fullCmd = "{} {}{}{}".format(cfg.cCommandBase, cmd, " " if len(args) > 0 else "", " ".join(args));
    log.debug("Processing sub-command: `%s`", fullCmd, extra=logExtra)
    if cmd == cfg.cCommandNewGame:
      if len(args) < 1:
        Error.DErr(logExtra, "Missing game code parameter in command `%s`", fullCmd)
      await self.NotifyAmongUsGame(logExtra, args[0])
    else:
      Error.DErr(logExtra, "Invalid sub-command `%s`: `%s`.", cmd, fullCmd)

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
          await member.send(content="You have been removed from `{}`'s Among Us players.".format(ctx.guild.name))
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
      "Notifying `@%s` of Among Us game code `%s` in %s",
      self.roleAmongUs.name,
      code,
      self.channelAmongUsCodes.mention)
    await self.channelAmongUsCodes.send(
      content="Attention {}! New game code: `{}`. Type `{}` if you no longer want to receive these notifications. {}".format(
        self.roleAmongUs.mention,
        code,
        cfg.cAmongUsLeaveRequestMessageText,
        cfg.cAmongUsSendGameNotificationText))
