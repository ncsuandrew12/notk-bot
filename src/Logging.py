# Standard
import datetime
import inspect
import re
import threading

# Local
from Config import cfg

def Log(lvl, msg):
  frame = inspect.currentframe()
  fn = re.sub(r'^.*/([^/]+py)$', '\g<1>', frame.f_code.co_filename)
  while fn.startswith("Logging") or fn == "Error.py":
    frame = frame.f_back
    fn = re.sub(r'^.*/([^/]+py)$', '\g<1>', frame.f_code.co_filename)
  threadName = threading.current_thread().name
  
  locationInfo = "{}:{}({})".format(
    re.sub(r'^.*/([^/]+py)$', '\g<1>', frame.f_code.co_filename),
    frame.f_code.co_name,
    frame.f_lineno)
  print("{} {} {} {} {} {} {}".format(
    datetime.datetime.now(),
    datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo,
    lvl + ((len("WARNING") - len(lvl)) * " "),
    cfg.cBotName.upper(),
    threadName + ((10 - len(threadName)) * " "),
    locationInfo,
    msg))

def Err(msg):
  Log("ERROR", msg)

def Warn(msg):
  Log("WARNING", msg)

def Info(msg):
  Log("INFO", msg)

def Debug(msg):
  Log("DEBUG", msg)
