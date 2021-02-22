# Modules
import discord
# import re
# import sys

# notk-bot
import Error
import Logging as log
import LoggingDiscord as dlog

from Config import cfg
from GuildBot import GuildBot
from Exceptions import MinorException
from Exceptions import NotkException

class NotkBot:
  def __init__(self, bot, token):
    self.bot = bot
    self.token = token

  def Run(self):
    log.debug("Starting root bot")
    self.guildBots = {}
    self.bot.run(self.token)

  async def OnReady(self):
    log.debug("Starting {} bots".format(len(self.bot.guilds)))

    for guild in self.bot.guilds:
      if guild.id in self.guildBots:
        continue

      guildBot = GuildBot()
      await guildBot.setup(self.bot.user, guild)
      self.guildBots[guild.id] = guildBot

    log.debug("{} bots running".format(len(self.guildBots)))

  async def Command(self, ctx, cmd, *args):
    try:
      if ctx.guild.id not in\
        self.guildBots:
        await Error.dErr(ctx, None, "`{}` has not been setup yet. This shouldn't be possible. Please contact the bot developer ({})".format(\
          ctx.guild.name,
          "andrewf#6219"))

      guildBot = self.guildBots[ctx.guild.id]
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
          await dlog.warn(guildBot, ctx, "Could not find `{}` members: `{}`!".format(ctx.guild.name, "`, `".join(missing)))

      if cmd == cfg.cCommandJoin:
        await guildBot.addAmongUsPlayer(ctx, members)
      elif cmd == cfg.cCommandLeave:
        await guildBot.removeAmongUsPlayer(ctx, members)
      elif cmd == cfg.cCommandNewGame:
        await guildBot.notifyAmongUsGame(ctx, ctx.message.channel, args[0])
      else:
        await Error.dErr(guildBot, ctx, "Invalid command `{}`.".format(cmd))
    except NotkException as e:
      # This error will have already been logged
      return
    except:
      raise
