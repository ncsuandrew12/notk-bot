# Modules
import discord
# import re
# import sys

# notk-bot
import Error
import Logging as log

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
      await guildBot.Command(ctx, cmd, *args)
    except NotkException as e:
      # This error will have already been logged
      return
    except:
      raise
