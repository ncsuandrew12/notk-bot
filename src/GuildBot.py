# Modules
import discord
import inspect
import re

# notk-bot
import Error
import Logging as log
import LoggingDiscord as dlog

from Config import cfg
from DiscordFacsimilies import AuthorStubbed
from DiscordFacsimilies import ContextStubbed

class GuildBot:
  def __init__(self, bot):
    self.bot = bot
    self.channelBot = None
    self.channelLog = None
    self.roleAmongUs = None

  async def setup(self, guild):
    roleMod = None

    ctx = ContextStubbed(guild, AuthorStubbed(guild.name))

    dlog.debug(ctx, "Starting {} (before channel located)".format(__name__))

    for channel in guild.channels:
      if channel.name == cfg.cBotChannelName:
        self.channelBot = channel
      elif channel.name == cfg.cLogChannelName:
        self.channelLog = channel
      else:
        continue
      dlog.debug(ctx, 'Found: {}'.format(channel.mention))

    # TODO delete
    # if bool(self.channelBot):
    #   await self.channelBot.delete(reason="pre-setup")
    #   guildBot.channelBot = None

    if not self.channelLog:
      dlog.debug(ctx, 'Creating {} log channel: `#{}`'.format(self.bot.user.mention, cfg.cLogChannelName))
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
      self.info(ctx, 'Created {} log channel: `#{}`'.format(self.bot.user.mention, self.channelLog.mention))

    await self.info(ctx, "Starting {}".format(__name__))

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
      # DO NOT mention the role. We don't need to tag all the players in this log message, lol.
      await self.info(ctx, 'Found: `@{}`'.format(role.name))

    # TODO Enable, but avoid sending messages to just whoever sent the command
    # if not roleMod:
    #   await dlog.warn(self, "{} role not found.".format(cfg.cRoleModPrefix))

    if not self.roleAmongUs:
      await self.info(ctx, 'Creating `@{}`'.format(cfg.cAmongUsRoleName))
      self.roleAmongUs = await guild.create_role(\
        name=cfg.cAmongUsRoleName,\
        mentionable=True,\
        hoist=False,\
        reason="Allow users to easily ping everyone interested in playing Among Us.")
        #colour=Colour.gold,\

    versionStr=""
    versionPath = 'VERSION'
    versionFile = open(versionPath, 'r')
    try:
      versionStr = versionFile.readline()
      if len(versionStr) < 3: # M.m
        await self.err(ctx, "Could not read version information from file: '{}'".format(versionPath))
    except:
      await self.err(ctx, "Could not read release notes from file: '{}'".format(versionPath))
    finally:
      versionFile.close()

    amongUsRoleMessage = None
    oldVersionStr = "0.0"
    if self.channelBot:
      # FIXME Parse all history until we find the instructional message
      for message in await self.channelBot.history(limit=1000).flatten():
        if (message.author.id == self.bot.user.id) &\
           ("⚠ notk-bot Instructions ⚠" in message.content.partition('\n')[0]):
          amongUsRoleMessage = message
          # await self.info(ctx, 'Found {} instructional message in {}: {}'.format(\
          #   amongUsRoleMessage.author.mention,\
          #   self.channelBot.mention,\
          #   amongUsRoleMessage.jump_url))
          match = re.search(r'Version ([0-9]+\.[0-9]+) Release Notes:', message.content)
          if match:
            oldVersionStr = match.group(1)
          break

    releaseNotes = ""
    releaseNotesPath = 'RELEASE_NOTES.md'
    releaseNotesFile = open(releaseNotesPath, 'r')
    releaseNotesLine = "nonnull"
    try:
      while releaseNotesLine:
        releaseNotesLine = releaseNotesFile.readline()
        if releaseNotesLine:
          releaseNotes += "\n" + releaseNotesLine
    except:
      await self.err(ctx, "Could not read release notes from file: '{}'".format(releaseNotesPath))
    finally:
      releaseNotesFile.close()

    # FUTURE include all past release note in the message (in descending order)
    amongUsRoleMessageText = \
    """⚠ notk-bot Instructions ⚠
Type `{}` in any public channel to be notified about NOTK Among Us game sessions.
Type `{}` in any public channel if you no longer want to be notified.
{}
Tag the `{}` role to ping all Among Us players like so: {}
I recommend muting the {} channel; it is only for logging purposes and will be very noisy.

Version {} Release Notes:{}
""".format(\
      cfg.cAmongUsJoinRequestMessageText,\
      cfg.cAmongUsLeaveRequestMessageText,\
      cfg.cAmongUsSendGameNotificationText,\
      cfg.cAmongUsRoleName,\
      self.roleAmongUs.mention,\
      self.channelLog.mention,\
      versionStr,\
      releaseNotes)

    if not self.channelBot:
      dlog.debug(ctx, 'Creating {} channel: `#{}`'.format(self.bot.user.mention, cfg.cBotChannelName))
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
      await self.info(ctx, 'Created {} channel: {}'.format(self.bot.user.mention, self.channelBot.mention))

      await self.channelBot.send(content="{}{} has added support for the Among Us player group via the {} role.".format(\
        roleMod.mention + ", " if roleMod else "",\
        self.bot.user.mention,\
        self.roleAmongUs.mention))

    if amongUsRoleMessage == None:
      await self.info(ctx, 'Sending `@{}` instructional message'.format(cfg.cAmongUsRoleName))
      amongUsRoleMessage = await self.channelBot.send(content=amongUsRoleMessageText)
    elif amongUsRoleMessage.content == amongUsRoleMessageText:
      # This should indicate that this is a simple restart.
      await self.info(ctx, 'Found up-to-date {} instructional message in {}: {}'.format(\
        amongUsRoleMessage.author.mention,\
        self.channelBot.mention,\
        amongUsRoleMessage.jump_url))
    else:
      await self.info(ctx, 'Updating old {} instructional message in {}: {}'.format(\
        amongUsRoleMessage.author.mention,\
        self.channelBot.mention,\
        amongUsRoleMessage.jump_url))
      await amongUsRoleMessage.edit(content=amongUsRoleMessageText)
      if (versionStr != oldVersionStr):
        await self.channelBot.send(content="{}{} has been updated!\nVersion {} Release Notes:\n{}\n".format(\
          roleMod.mention + ", " if roleMod else "",\
          self.bot.user.mention,\
          versionStr,\
          releaseNotes))
    
    if amongUsRoleMessage.pinned:
      await self.info(ctx, '`@{}` instructional message already pinned.'.format(cfg.cAmongUsRoleName))
    else:
      await self.info(ctx, 'Pinning `@{}` instructional message'.format(cfg.cAmongUsRoleName))
      await amongUsRoleMessage.pin(reason="The `@{}` instructional message needs to be very visible to be useful".format(cfg.kBotName))

    await self.info(ctx, "{} started.".format(__name__))

  async def Command(self, ctx, cmd, *args):
    dlog.debug(ctx, "Processing command: `{} {}`".format(cmd, " ".join(args)))

    members = []
    memberNames = []
    resolved = []
    if cmd in [ cfg.cCommandJoin, cfg.cCommandLeave]:
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
            dlog.serverWarn(ctx, "userID `{}`: {}".format(userID, str(e)))
          except:
            dlog.serverWarn(ctx, "userID `{}`: {}".format(userID, str(sys.exc_info()[0])))
          else:
            if member.name not in memberNames:
              resolved.append(userIDs[userID])
              members.append(member)
              memberNames.append(member.name)
      else:
        member = await ctx.guild.fetch_member(ctx.author.id)
        members = [member]
        memberNames = [member.name]
      missing = set(args) - set(resolved)
      if (len(missing) > 0):
        await dlog.warn(self, ctx, "Could not find `{}` members: `{}`!".format(ctx.guild.name, "`, `".join(missing)))

    if cmd == cfg.cCommandJoin:
      await self.AddAmongUsPlayer(ctx, members)
    elif cmd == cfg.cCommandLeave:
      await self.RemoveAmongUsPlayer(ctx, members)
    elif cmd == cfg.cCommandNewGame:
      await self.NotifyAmongUsGame(ctx, ctx.message.channel, args[0])
    else:
      await Error.dErr(self, ctx, "Invalid command `{}`.".format(cmd))

  async def AddAmongUsPlayer(self, ctx, members):
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

  async def RemoveAmongUsPlayer(self, ctx, members):
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

  async def NotifyAmongUsGame(self, ctx, channel, code):
    match = re.compile(r'^([A-Za-z]{6})$').search(code)
    if not match:
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

