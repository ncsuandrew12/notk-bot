# Modules

# notk-bot
import Logging as log

async def dLog(guildBot, ctx, lvl, msg):
  sLog(ctx, lvl, msg)
  if bool(guildBot.channelLog):
    await guildBot.channelLog.send(content="{}: {}: {}".format(lvl, ctx.author.name, msg))

async def err(guildBot, ctx, msg):
  await logSevere(guildBot, ctx, "ERROR", msg)

async def warn(guildBot, ctx, msg):
  await logSevere(guildBot, ctx, "WARNING", msg)

async def info(guildBot, ctx, msg):
  await dLog(guildBot, ctx, "INFO", msg)

def debug(ctx, msg):
  sDebug(ctx, msg)

def sLog(ctx, lvl, msg):
  log.log(lvl, "{}.{}: {}".format(ctx.guild.name, ctx.author.name, msg))

async def logSevere(guildBot, ctx, lvl, msg):
  sLog(ctx, lvl, msg)
  if bool(guildBot.channelLog):
    await guildBot.channelLog.send(\
      content="{}: {}: {}".format(\
        ctx.author.mention if bool(ctx.author.mention) else ctx.author.name,\
        lvl,
        msg))
  elif not ctx.author.bot:
    await ctx.author.send(msg)

def sErr(ctx, msg):
  sLog(ctx, "ERROR", msg)

def sWarn(ctx, msg):
  sLog(ctx, "WARNING", msg)

def sInfo(ctx, msg):
  sLog(ctx, "INFO", msg)

def sDebug(ctx, msg):
  sLog(ctx, "DEBUG", msg)
