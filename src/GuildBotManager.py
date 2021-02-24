# Modules
import asyncio
import discord
import inspect

# notk-bot
import Error
import Logging as log

from GuildBot import GuildBot
from Exceptions import MinorException
from Exceptions import NotkException

class GuildBotManager:
  def __init__(self, bot, token):
    self.bot = bot
    self.token = token

  def Run(self):
    log.info("Starting {}".format(__name__))
    self.guildBots = {}
    self.bot.run(self.token)
    log.info("Exiting {}".format(__name__))

  async def OnReady(self):
    log.debug("Starting {} {}".format(len(self.bot.guilds), GuildBot.__name__))

    # TODO start the separate guild bots asynchronously
    for guild in self.bot.guilds:
      if guild.id in self.guildBots:
        continue

      guildBot = GuildBot(self.bot)
      await guildBot.setup(guild)
      self.guildBots[guild.id] = guildBot

    log.debug("{} guild bots running".format(len(self.guildBots)))

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
