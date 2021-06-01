# Standard

# Local
from Logging import logger as log
from Exceptions import MinorException
from Exceptions import NotkException

import LoggingDiscord as dlog

def Err(msg):
  log.error(msg)
  raise NotkException(msg)

def DErr(ctx, msg, *args):
  dlog.Err(ctx, msg, *args)
  raise NotkException(msg)

def ErrMinor(ctx, msg, *args):
  dlog.Err(ctx, msg, *args)
  raise MinorException(msg)
