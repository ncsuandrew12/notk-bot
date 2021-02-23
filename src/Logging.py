# Modules

# notk-bot
from Config import cfg

def log(msg):
  print("{}| {}".format(cfg.kBotName.upper(), msg))

def info(msg):
  log("INFO:    {}".format(msg))

def error(msg):
  log("ERROR:   {}".format(msg))

def debug(msg):
  log("DEBUG:   {}".format(msg))
