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
  # TODO classname
    # datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo,
  print("{} {} {} {} {} {}:{} {}{}| {}".format(
    datetime.datetime.now(),
    datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo,
    threadName + ((10 - len(threadName)) * " "),
    lvl + ((len("WARNING") - len(lvl)) * " "),
    cfg.cBotName.upper(),
    re.sub(r'^.*/([^/]+py)$', '\g<1>', frame.f_code.co_filename),
    frame.f_lineno,
    "",
    frame.f_code.co_name,
    msg))

def Err(msg):
  Log("ERROR", msg)

def Warn(msg):
  Log("WARNING", msg)

def Info(msg):
  Log("INFO", msg)

def Debug(msg):
  Log("DEBUG", msg)
