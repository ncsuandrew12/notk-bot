# Modules
import discord
import os

from discord.ext import commands

# notk-bot
from Config import cfg
from NotkBot import NotkBot
import Logging as log

# Get function name
#import inspect
# inspect.currentframe().f_code.co_name

# Needed to be able to list members (for mapping member name arguments to actual members)
kIntents = discord.Intents.default()
kIntents.members = True

tokenFilePath = 'cfg/discord.token'
if os.path.exists(tokenFilePath):
  tokenFile = open(tokenFilePath, 'r')
  try:
    token = tokenFile.readline()
  except:
    log.err("Could not read token from file: '{}'".format(tokenFilePath))
    raise
  finally:
    tokenFile.close()
else:
  token = os.getenv('TOKEN')

bot = commands.Bot(command_prefix=cfg.cCommandPrefix, intents=kIntents)

notkBot = NotkBot(bot, token)

@bot.event
async def on_ready():
  await notkBot.OnReady()

@bot.command()
async def au(ctx, cmd, *args):
  await notkBot.Command(ctx, cmd, *args)

try:
  notkBot.Run()
except Exception as e:
  Logging.log.err("Error while running bot: {}".format(e))
  raise
except:
  Logging.log.err("Error while running bot!")
  raise