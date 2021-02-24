# Modules
import discord
import json

from discord.ext import commands

# notk-bot
import Logging as log

from Config import cfg
from GuildBotManager import GuildBotManager

# Needed to be able to list members (for mapping member name arguments to actual members)
kIntents = discord.Intents.default()
kIntents.members = True

bot = commands.Bot(command_prefix=cfg.cCommandPrefix, intents=kIntents)

notkBot = GuildBotManager(bot, cfg.cToken)

@bot.event
async def on_ready():
  await notkBot.OnReady()

@bot.command()
async def au(ctx, cmd, *args):
  await notkBot.Command(ctx, cmd, *args)

try:
  notkBot.Run()
except Exception as e:
  log.error("Error while running bot: {}".format(e))
  raise
except:
  log.error("Error while running bot!")
  raise