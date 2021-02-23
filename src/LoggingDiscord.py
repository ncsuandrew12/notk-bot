# Modules
# import discord

# notk-bot
# import GuildBot
import Logging

async def log(guildBot, ctx, msg):
  serverLog(ctx, msg)
  if bool(guildBot.channelLog):
    await guildBot.channelLog.send(content="{}".format("{}: {}".format(ctx.author.name, msg)))

async def err(guildBot, ctx, msg):
  await logSevere(guildBot, ctx, "ERROR:   {}".format(msg))

async def warn(guildBot, ctx, msg):
  await logSevere(guildBot, ctx, "WARNING: {}".format(msg))

async def info(guildBot, ctx, msg):
  await log(guildBot, ctx, "INFO:    {}".format(msg))

def debug(ctx, msg):
  serverLog(ctx, "DEBUG:   {}".format(msg))

def serverLog(ctx, msg):
  Logging.log("{}.{}: {}".format(ctx.guild.name, ctx.author.name, msg))

def serverError(ctx, msg):
  serverLog(ctx, "ERROR:   {}".format(msg))

def serverWarn(ctx, msg):
  serverLog(ctx, "WARNING: {}".format(msg))

def serverInfo(ctx, msg):
  serverLog(ctx, "INFO:    {}".format(msg))

async def logSevere(guildBot, ctx, msg):
  serverLog(ctx, msg)
  if bool(guildBot.channelLog):
    await guildBot.channelLog.send(\
      content="{}: {}".format(\
        ctx.author.mention if bool(ctx.author.mention) else ctx.author.name,\
        msg))
  elif not ctx.author.bot:
    await ctx.author.send(msg)
