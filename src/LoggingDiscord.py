# Local
import Logging as log

def DLog(guildBot, ctx, lvl, msg):
  SLog(ctx, lvl, msg)
  if bool(guildBot.channelLog):
    guildBot.loop.create_task(guildBot.channelLog.send(content="{}: {}: {}".format(lvl, ctx.author.name, msg)))

def Err(guildBot, ctx, msg):
  SLogSevere(guildBot, ctx, "ERROR", msg)

def Warn(guildBot, ctx, msg):
  SLogSevere(guildBot, ctx, "WARNING", msg)

def Info(guildBot, ctx, msg):
  DLog(guildBot, ctx, "INFO", msg)

def Debug(ctx, msg):
  SDebug(ctx, msg)

def SLog(ctx, lvl, msg):
  log.Log(lvl, "{}.{}: {}".format(ctx.guild.name, ctx.author.name, msg))

def SLogSevere(guildBot, ctx, lvl, msg):
  SLog(ctx, lvl, msg)
  if bool(guildBot.channelLog):
    guildBot.loop.create_task(guildBot.channelLog.send(
      content="{}: {}: {}".format(
        ctx.author.mention if bool(ctx.author.mention) else ctx.author.name,
        lvl,
        msg)))
  elif not ctx.author.bot:
    guildBot.loop.create_task(ctx.author.send(msg))

def SErr(ctx, msg):
  SLog(ctx, "ERROR", msg)

def SWarn(ctx, msg):
  SLog(ctx, "WARNING", msg)

def SInfo(ctx, msg):
  SLog(ctx, "INFO", msg)

def SDebug(ctx, msg):
  SLog(ctx, "DEBUG", msg)
