# Standard
import logging

# Local
from Logging import logger as log

def DLog(ctx, lvl, msg, *args):
  # The same ctx object is also used for a number of direct logger.<level>() calls which expect serverLog to be False.
  # Therefore, make a copy of it before modifying serverLog.
  # TODO Find some way to avoid this and delete these functions.
  extra = ctx
  extra.serverLog = True
  log.log(lvl, msg, *args, extra=extra)

def Err(ctx, msg, *args):
  DLog(ctx, logging.ERROR, msg, *args)

def Warn(ctx, msg, *args):
  DLog(ctx, logging.WARNING, msg, *args)

def Info(ctx, msg, *args):
  DLog(ctx, logging.INFO, msg, *args)
