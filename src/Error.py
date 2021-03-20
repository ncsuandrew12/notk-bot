# Standard

# Local
from Exceptions import MinorException
from Exceptions import NotkException

import LoggingDiscord as dlog
import Logging as log

def Err(msg):
  log.Err(msg)
  raise NotkException(msg)

async def DErr(guildBot, ctx, msg):
  await dlog.Err(guildBot, ctx, msg)
  raise NotkException(msg)

async def ErrMinor(guildBot, ctx, msg):
  await dlog.Err(guildBot, ctx, msg)
  raise MinorException(msg)
