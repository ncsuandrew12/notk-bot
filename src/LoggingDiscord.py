# Modules

# Local
import Logging as log

async def DLog(guildBot, ctx, lvl, msg):
  SLog(ctx, lvl, msg)
  if bool(guildBot.channelLog):
    await guildBot.channelLog.send(content="{}: {}: {}".format(lvl, ctx.author.name, msg))

async def Err(guildBot, ctx, msg):
  await SLogSevere(guildBot, ctx, "ERROR", msg)

async def Warn(guildBot, ctx, msg):
  await SLogSevere(guildBot, ctx, "WARNING", msg)

async def Info(guildBot, ctx, msg):
  await DLog(guildBot, ctx, "INFO", msg)

def Debug(ctx, msg):
  SDebug(ctx, msg)

def SLog(ctx, lvl, msg):
  log.Log(lvl, "{}.{}: {}".format(ctx.guild.name, ctx.author.name, msg))

async def SLogSevere(guildBot, ctx, lvl, msg):
  SLog(ctx, lvl, msg)
  if bool(guildBot.channelLog):
    await guildBot.channelLog.send(\
      content="{}: {}: {}".format(\
        ctx.author.mention if bool(ctx.author.mention) else ctx.author.name,\
        lvl,
        msg))
  elif not ctx.author.bot:
    await ctx.author.send(msg)

def SErr(ctx, msg):
  SLog(ctx, "ERROR", msg)

def SWarn(ctx, msg):
  SLog(ctx, "WARNING", msg)

def SInfo(ctx, msg):
  SLog(ctx, "INFO", msg)

def SDebug(ctx, msg):
  SLog(ctx, "DEBUG", msg)
