# Modules
import discord
import sys

from discord.ext import commands
from sys import argv

# notk-bot
import Logging as log
import UtilBot

from Config import cfg

kIntents = discord.Intents.default()
kIntents.members = True

bot = commands.Bot(command_prefix=cfg.cCommandPrefix, intents=kIntents)
utilBot = UtilBot.UtilBot(bot, *argv[1:])

@bot.event
async def on_ready():
  global utilBot

  errCode = 0

  try:
    log.debug("Ready")
    await utilBot.OnReady()
    await utilBot.RunCommand()
  except NotkException as e:
    errCode = 1
  except Exception as e:
    log.error("Error while running command! {}".format(e))
    errCode = 1

  try:
    await utilBot.Close()
  except NotkException as e:
    if errCode == 0:
      errCode = 2
  except Exception as e:
    log.error("Error while closing bot! {}".format(e))
    if errCode == 0:
      errCode = 2

  if (errCode != 0):
    sys.exit(errCode)

def run():
  global utilBot

  errCode = 0

  try:
    utilBot.Run()
  except NotkException as e:
    errCode = 1
  except Exception as e:
    log.error("Error while running bot! {}".format(e))
    errCode = 1

  if (errCode != 0):
    sys.exit(errCode)

run()
