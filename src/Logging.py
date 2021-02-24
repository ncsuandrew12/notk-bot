# Modules
import inspect
import re

# notk-bot
from Config import cfg

def log(lvl, msg):
  frame = inspect.currentframe()
  while (re.sub(r'^.*/([^/]+py)$', '\g<1>', frame.f_code.co_filename).startswith("Logging")):
    frame = frame.f_back
  print("{}| {}{}:{} {}{} {}".format(\
    cfg.kBotName.upper(),\
    lvl + ":" + ((len("WARNING: ") - len(lvl) - 1) * " "),
    re.sub(r'^.*/([^/]+py)$', '\g<1>', frame.f_code.co_filename),\
    frame.f_lineno,\
    "",\
    frame.f_code.co_name,\
    msg))

def error(msg):
  log("ERROR", msg)

def warn(msg):
  log("WARNING", msg)

def info(msg):
  log("INFO", msg)

def debug(msg):
  log("DEBUG", msg)
