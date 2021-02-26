# Modules
import asyncio
import discord
import inspect

from discord.ext import commands
from inspect import currentframe, getframeinfo

# notk-bot
import Error
import Logging as log

from Config import cfg
from GuildBot import GuildBot
from Exceptions import MinorException
from Exceptions import NotkException

class GuildBotManager:
  def __init__(self, bot, loop, token):
    self.bot = bot
    self.token = token
    self.loop = loop

  def Run(self):
    log.info("Starting up")
    self.guildBots = {}
    self.loop.create_task(self.bot.start(self.token))

  def RunForever(self):
    try:
      self.Run()
      self.WaitUntilReady()
      self.OnReady()
      self.StartGuildBots()
      self.SetupGuilds()
      self.loop.run_forever()
    except Exception as e:
      log.err("Error while running bot: {}".format(e))
      raise
    except:
      log.err("Error while running bot!")
      raise
    finally:
      self.loop.close()

  def Close(self):
    log.debug("Shutting down")
    self.loop.run_until_complete(self.bot.logout()) #close?

  def WaitUntilReady(self):
    self.loop.run_until_complete(self.bot.wait_until_ready())
    log.info("Bot is ready")

  def OnReady(self):
    for guild in self.bot.guilds:
      guildBot = GuildBot(self.bot, guild, self.loop)
      self.guildBots[guild.id] = guildBot

  def StartGuildBots(self):
    log.debug("Starting {} {}".format(len(self.bot.guilds), GuildBot.__name__))

    for guild in self.bot.guilds:
      self.loop.run_until_complete(self.guildBots[guild.id].startup())

    log.debug("{} {} running".format(len(self.guildBots), GuildBot.__name__))

  def SetupGuilds(self):
    log.debug("Setting up {} guilds".format(len(self.bot.guilds)))

    for guild in self.bot.guilds:
      self.loop.run_until_complete(self.guildBots[guild.id].setup())

    log.debug("{} guilds set up".format(len(self.guildBots)))

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

# Needed to be able to list members (for mapping member name arguments to actual members)
kIntents = discord.Intents.default()
kIntents.members = True

discordBot = commands.Bot(command_prefix=cfg.cCommandPrefix, intents=kIntents)
bot = GuildBotManager(discordBot, asyncio.get_event_loop(), cfg.cToken)

@discordBot.command()
async def au(ctx, cmd, *args):
  await bot.Command(ctx, cmd, *args)
