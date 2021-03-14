# Modules
import inspect
import re

# notk-bot
from Config import cfg

def Log(lvl, msg):
  frame = inspect.currentframe()
  while (re.sub(r'^.*/([^/]+py)$', '\g<1>', frame.f_code.co_filename).startswith("Logging")):
    frame = frame.f_back

  # TODO classname
  print("{}| {}{}:{} {}{}| {}".format(\
    cfg.cBotName.upper(),\
    lvl + ":" + ((len("WARNING: ") - len(lvl) - 1) * " "),
    re.sub(r'^.*/([^/]+py)$', '\g<1>', frame.f_code.co_filename),\
    frame.f_lineno,\
    "",\
    frame.f_code.co_name,\
    msg))

def Err(msg):
  Log("ERROR", msg)

def Warn(msg):
  Log("WARNING", msg)

def Info(msg):
  Log("INFO", msg)

def Debug(msg):
  Log("DEBUG", msg)
