# Modules

# notk-bot
import Logging as log

async def dLog(guildBot, ctx, msg):
  sLog(ctx, msg)
  if bool(guildBot.channelLog):
    await guildBot.channelLog.send(content="{}".format("{}: {}".format(ctx.author.name, msg)))

async def err(guildBot, ctx, msg):
  await logSevere(guildBot, ctx, "ERROR:   {}".format(msg))

async def warn(guildBot, ctx, msg):
  await logSevere(guildBot, ctx, "WARNING: {}".format(msg))

async def info(guildBot, ctx, msg):
  await dLog(guildBot, ctx, "INFO:    {}".format(msg))

def debug(ctx, msg):
  sDebug(ctx, msg)

def sLog(ctx, msg):
  log.log("{}.{}: {}".format(ctx.guild.name, ctx.author.name, msg))

async def logSevere(guildBot, ctx, msg):
  sLog(ctx, msg)
  if bool(guildBot.channelLog):
    await guildBot.channelLog.send(\
      content="{}: {}".format(\
        ctx.author.mention if bool(ctx.author.mention) else ctx.author.name,\
        msg))
  elif not ctx.author.bot:
    await ctx.author.send(msg)

def sErr(ctx, msg):
  sLog(ctx, log.labelError(msg))

def sWarn(ctx, msg):
  sLog(ctx, log.labelWarn(msg))

def sInfo(ctx, msg):
  sLog(ctx, log.labelInfo(msg))

def sDebug(ctx, msg):
  sLog(ctx, log.labelDebug(msg))
