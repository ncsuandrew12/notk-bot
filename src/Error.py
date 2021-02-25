# Modules

# notk-bot
from Exceptions import MinorException
from Exceptions import NotkException

import LoggingDiscord as dlog
import Logging as log

def err(msg):
  log.err(msg)
  raise NotkException(msg)

async def dErr(guildBot, ctx, msg):
  await dlog.err(guildBot, ctx, msg)
  raise NotkException(msg)

async def errMinor(guildBot, ctx, msg):
  await dlog.err(guildBot, ctx, msg)
  raise MinorException(msg)
