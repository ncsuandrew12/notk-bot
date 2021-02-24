# Modules

# notk-bot
from Config import cfg

def log(msg):
  print("{}| {}".format(cfg.kBotName.upper(), msg))

def label(lbl, msg):
  return lbl + ":" + ((len("WARNING: ") - len(lbl) - 1) * " ") + msg

def labelError(msg):
  return label("ERROR", msg)

def labelWarn(msg):
  return label("WARNING", msg)

def labelInfo(msg):
  return label("INFO", msg)

def labelDebug(msg):
  return label("DEBUG", msg)

def error(msg):
  log(labelError(msg))

def warn(msg):
  log(labelWarn(msg))

def info(msg):
  log(labelInfo(msg))

def debug(msg):
  log(labelDebug(msg))
