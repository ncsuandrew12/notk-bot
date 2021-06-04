# Standard
import asyncio
import inspect
import traceback
from inspect import currentframe, getframeinfo

# Modules
import discord
from discord.ext import commands

# Local
import Error
import Logging
from Config import cfg
from Database import Database
from Exceptions import MinorException
from Exceptions import NotkException
from GuildBot import GuildBot
from Logging import logger as log

# Needed to be able to list members (for mapping member name arguments to actual members)
kIntents = discord.Intents.default()
kIntents.members = True

discordBot = commands.Bot(command_prefix=cfg.cCommandPrefix, intents=kIntents)

class GuildBotManager:
  def __init__(self, loop, token):
    self.token = token
    self.loop = loop
    self.database = Database(self.loop)

  def Start(self):
    log.info("Starting up")
    self.database.Connect()
    self.database.Setup()
    self.guildBots = {}
    self.loop.create_task(discordBot.start(self.token))

  def Run(self):
    try:
      self.Start()
      self.WaitUntilReady()
      self.StartGuildBots()
      self.SetupGuildBots()
    except Exception as e:
      log.error("Error while running bot: %s", e)
      log.exception(e)
      self.Shutdown()
      raise
    except:
      log.error("Error while running bot!")
      self.Shutdown()
      raise

  def RunForever(self):
    try:
      self.Run()
      self.loop.run_forever()
    except Exception as e:
      log.error("Error while running bot: %s", e)
      log.exception(e)
      raise
    except:
      log.error("Error while running bot!")
      raise
    finally:
      self.Shutdown()

  def Shutdown(self):
    log.debug("Shutting down")
    try:
      for guild in discordBot.guilds:
        self.ShutdownGuild(guild)
      self.guildBots = {}
      if not discordBot.is_closed():
        self.loop.run_until_complete(discordBot.close())
      discordBot.clear()
      self.database.Close()
    except Exception as e:
      log.error("Error while closing Discord command Bot: %s", e)
      log.exception(e)
      raise
    except:
      log.error("Error while closing Discord command Bot!")
      raise

  def ShutdownGuild(self, guild):
    try:
      shutdown = self.guildBots[guild.id].Shutdown()
      if not shutdown:
        Error.Err("Failed to update {}'s status (shutdown)".format(guild.name))
    except Exception as e:
      log.error("Error while shutting down %s's bot: %s", guild.name, e)
      log.exception(e)
      traceback.print_exc()
    except:
      log.error("Error while shutting down %s's bot!", guild.name)

  def WaitUntilReady(self):
    log.info("Waiting until ready")
    self.loop.run_until_complete(discordBot.wait_until_ready())
    log.info("%s is ready", commands.Bot.__name__)

  def StartGuildBots(self):
    for guild in discordBot.guilds:
      guildBot = GuildBot(discordBot, guild, self.loop, self.database)
      self.guildBots[guild.id] = guildBot
    log.debug("Starting %d %s", len(discordBot.guilds), GuildBot.__name__)
    tasks = []
    for guild in discordBot.guilds:
      tasks.append(self.guildBots[guild.id].Startup())
    self.loop.run_until_complete(asyncio.gather(*tasks))
    log.debug("%d %s running", len(self.guildBots), GuildBot.__name__)

  def SetupGuildBots(self):
    log.debug("Setting up %d guilds", len(discordBot.guilds))
    tasks = []
    for guild in discordBot.guilds:
      tasks.append(self.guildBots[guild.id].Setup())
    self.loop.run_until_complete(asyncio.gather(*tasks))
    log.debug("%d guilds set up", len(self.guildBots))

  async def Command(self, cmd, logExtra=None, args=[]):
    log.debug("Command: %s %s", cmd, " ".join(args))
    try:
      if logExtra.discordContext.guild.id not in self.guildBots:
        Error.DErr(
          logExtra.discordContext,
          "`%s` has not been setup yet. This shouldn't be possible. Please contact the bot developer (%s)",
          logExtra.discordContext.guild.name,
          "andrewf#6219")

      guildBot = self.guildBots[logExtra.discordContext.guild.id]
      await self.loop.create_task(guildBot.Command(cmd, logExtra, args))
    except NotkException as e:
      # This error will have already been logged
      return
    except:
      raise

notkBot = GuildBotManager(asyncio.get_event_loop(), cfg.cToken)

@discordBot.command()
async def au(ctx, cmd, *args):
  await notkBot.Command(cmd, Logging.LogExtra(ctx), args)