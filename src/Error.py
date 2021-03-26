# Standard

# Local
from Exceptions import MinorException
from Exceptions import NotkException

import LoggingDiscord as dlog
import Logging as log

def Err(msg):
  log.Err(msg)
  raise NotkException(msg)

def DErr(guildBot, ctx, msg):
  dlog.Err(guildBot, ctx, msg)
  raise NotkException(msg)

def ErrMinor(guildBot, ctx, msg):
  dlog.Err(guildBot, ctx, msg)
  raise MinorException(msg)
