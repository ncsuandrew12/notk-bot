# Standard
import datetime
import inspect
import logging
import os
# import pathlib
import re
import sys
import threading
from logging.handlers import RotatingFileHandler

# Local
from Config import cfg

class MaxLogLevelFilter(logging.Filter):
  def __init__(self, logLevel):
    self.logLevel = logLevel
  def filter(self, record):
    return record.levelno <= self.logLevel
  logLevel = logging.DEBUG

class DiscordLogFilter(logging.Filter):
  # TODO Filter by ID instead of name
  def __init__(self, guildName):
    self.guildName = guildName
  def filter(self, record):
    return (
      hasattr(record, 'discordContext') and
      record.serverLog == True and
      self.guildName == record.discordContext.guild.name)

class LocalFormatter(logging.Formatter):
  def format(self, record):
    frame = inspect.currentframe()
    fn = re.sub(r'^.*/([^/]+py)$', '\g<1>', frame.f_code.co_filename)
    while frame.f_back and (fn.startswith("Logging") or fn == "Error.py" or fn == "__init__.py" or fn == "handlers.py"):
      frame = frame.f_back
      fn = re.sub(r'^.*/([^/]+py)$', '\g<1>', frame.f_code.co_filename)

    record.timeZone = datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo
    record.levelnamePadding = (" " * (len("CRITICAL") - len(record.levelname)))
    record.botName = cfg.cBotName.upper()
    record.callerFilename = re.sub(r'^.*/([^/]+py)$', '\g<1>', frame.f_code.co_filename)
    record.callerLineNum = frame.f_lineno
    record.callerFuncName = frame.f_code.co_name

    record.discordMemberPrefix = ""
    if hasattr(record, 'discordContext'):
      record.discordMemberPrefix = " " + record.discordContext.guild.name + "." + record.discordContext.author.name + ":"

    return logging.Formatter.format(self, record)

class DiscordLogChannelFormatter(logging.Formatter):
  def format(self, record):
    record.timeZone = datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo
    record.levelnamePadding = (" " * (len("CRITICAL") - len(record.levelname)))
    record.authorMention = record.discordContext.author.mention
    return logging.Formatter.format(self, record)

class DiscordLogChannelHandler(logging.StreamHandler):
  def __init__(self, guildBot):
    logging.StreamHandler.__init__(self)
    self.guildBot = guildBot
    self.addFilter(DiscordLogFilter(guildBot.guild.name))

  def emit(self, record):
    if bool(self.guildBot.channelLog):
      # print("amf: emitting to channel")
      self.guildBot.loop.create_task(self.guildBot.channelLog.send(content=self.format(record)))
    elif hasattr(record, 'author') and not record.author.bot:
      # print("amf: emitting to user")
      self.guildBot.loop.create_task(record.author.send(self.format(record)))
    # else:
    #   print("amf: not emitting")

class LogExtra:
  def __init__(self, discordContext):
    self.discordContext = discordContext
    self.serverLog = False

  def __iter__(self):
    return LogExtraIterator()

  def __getitem__(self, key):
    if key == "discordContext":
      return self.discordContext
    if key == "serverLog":
      return self.serverLog
    raise KeyError(key)

class LogExtraIterator:
  _keys = [ 'discordContext', 'serverLog' ]

  def __init__(self):
    self._index = 0

  def __next__(self):
    if self._index < len(self._keys):
      key = self._keys[self._index]
      self._index += 1
      return key
    raise StopIteration

localFormatter = LocalFormatter(
  # %(processName)s
  fmt="%(asctime)s %(timeZone)s %(levelname)s%(levelnamePadding)s %(botName)s %(threadName)s %(callerFilename)s:%(callerFuncName)s(%(callerLineNum)d)%(discordMemberPrefix)s %(message)s",
  datefmt=None)
discordLogChannelFormatter = DiscordLogChannelFormatter(
  fmt="`%(asctime)s %(timeZone)s %(levelnamePadding)s%(levelname)s` %(authorMention)s: %(message)s",
  datefmt=None)

def SetupLogger(title):
  logDir = "./log/{}".format(title)
  if not os.path.exists(logDir):
    print("Making logDir: " + logDir)
    os.makedirs(logDir)

  # Create log handlers
  stdoutHandler = logging.StreamHandler(stream=sys.stdout)
  stderrHandler = logging.StreamHandler(stream=sys.stderr)
  mainFileHandler = RotatingFileHandler(
    filename="{}/log.log".format(logDir),
    maxBytes=5 * 1024 * 1024, # 5MB
    backupCount=9,
    delay=True)
  errFileHandler = RotatingFileHandler(
    filename="{}/err.log".format(logDir),
    maxBytes=5 * 1024 * 1024, # 5MB
    backupCount=1,
    delay=True)

  # Configure formatters
  stdoutHandler.setFormatter(localFormatter)
  stderrHandler.setFormatter(localFormatter)
  mainFileHandler.setFormatter(localFormatter)
  errFileHandler.setFormatter(localFormatter)

  # Configure log levels
  logging.getLogger().setLevel(logging.NOTSET) # Enable all logging levels in general
  stdoutHandler.setLevel(logging.NOTSET) # Set no minimum logging level for console output
  stdoutHandler.addFilter(MaxLogLevelFilter(logging.WARNING)) # Skip ERROR logs for standard console output
  stderrHandler.setLevel(logging.ERROR) # Skip non-ERROR logs for standard error output
  mainFileHandler.setLevel(logging.NOTSET) # Include all logs in main log file
  errFileHandler.setLevel(logging.WARNING) # Skip sub-WARNING logs for error log file

  logger = logging.getLogger(title)

  # Add all handlers to logger
  logger.addHandler(stdoutHandler)
  logger.addHandler(stderrHandler)
  logger.addHandler(mainFileHandler)
  logger.addHandler(errFileHandler)

  return logger

logger = SetupLogger("notkbot")