# Modules
import asyncio
import discord
import inspect

from discord.ext import commands
from inspect import currentframe, getframeinfo

# notk-bot
import Error
import Logging as log
import Util

from Config import cfg
from Database import Database
from GuildBot import GuildBot
from Exceptions import MinorException
from Exceptions import NotkException

# Needed to be able to list members (for mapping member name arguments to actual members)
kIntents = discord.Intents.default()
kIntents.members = True

discordBot = commands.Bot(command_prefix=cfg.cCommandPrefix, intents=kIntents)

class GuildBotManager:
  def __init__(self, loop, token):
    self.token = token
    self.loop = loop
    self.database = Database(self.loop)

  def Run(self):
    log.info("Starting up")
    self.database.Connect()
    self.database.Setup()
    self.database.StartBot()
    self.guildBots = {}
    self.loop.create_task(discordBot.start(self.token))

  def RunForever(self):
    try:
      self.Run()
      self.WaitUntilReady()
      self.OnReady()
      self.StartGuildBots()
      self.SetupGuilds()
      self.database.BotStarted()
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
    self.database.ShutdownBot()
    self.loop.run_until_complete(discordBot.close())
    discordBot.clear()
    self.guildBots = {}
    log.debug("Shut down")

  def WaitUntilReady(self):
    log.info("Waiting until ready")
    self.loop.run_until_complete(discordBot.wait_until_ready())
    log.info("Bot is ready")

  def OnReady(self):
    for guild in discordBot.guilds:
      guildBot = GuildBot(discordBot, guild, self.loop)
      self.guildBots[guild.id] = guildBot

  def StartGuildBots(self):
    log.debug("Starting {} {}".format(len(discordBot.guilds), GuildBot.__name__))

    tasks = []
    for guild in discordBot.guilds:
      tasks.append(self.loop.create_task(self.guildBots[guild.id].startup()))

    Util.WaitForTasks(self.loop, tasks)

    log.debug("{} {} running".format(len(self.guildBots), GuildBot.__name__))

  def SetupGuilds(self):
    log.debug("Setting up {} guilds".format(len(discordBot.guilds)))

    for guild in discordBot.guilds:
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

notkBot = GuildBotManager(asyncio.get_event_loop(), cfg.cToken)

@discordBot.command()
async def au(ctx, cmd, *args):
  await notkBot.Command(ctx, cmd, *args)