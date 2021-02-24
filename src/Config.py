# Modules
import json
import os

# notk-bot

class Config:
  def __init__(self, configFilename):
    self.cCommandJoin = "join"
    self.cCommandLeave = "leave"
    self.cCommandNewGame = "newgame"
    self.cExternalChanges = "EXTERNAL CHANGES"
    self.cInstructionalLine = "⚠ notk-bot Instructions ⚠"
    self.cReleaseNotes = "Release Notes:"
    self.cRoleModPrefix = "mod"
    self.cRoleModSubstring = "moderator"

    cCommandRoot = "au" # Must match the @bot.commmand() function name

    self.kBotName = "notk-bot"

    with open(configFilename) as file:
      config = json.load(file)

    unviersalSuffix = config["universalSuffix"]
    secretsFile = "cfg/" + config["secretFile"]

    self.kBotName += "{}".format(unviersalSuffix)

    self.cAmongUsRoleName = "among-us{}".format(unviersalSuffix)
    self.cBotChannelName = self.kBotName
    self.cLogChannelName = "{}-log".format(self.cBotChannelName)

    self.cCommandPrefix=config["commandPrefix"]

    cCommandBase = "{}{}".format(self.cCommandPrefix, cCommandRoot)

    self.cAmongUsJoinRequestMessageText = "{} {}".format(cCommandBase, self.cCommandJoin)
    self.cAmongUsLeaveRequestMessageText = "{} {}".format(cCommandBase, self.cCommandLeave)
    self.cAmongUsSendGameNotificationText =\
      "Type `{} {} <room-code>` in any public channel to send a new game notification.".format(\
        cCommandBase,\
        self.cCommandNewGame)

    try:
      tokenFile = open(secretsFile, 'r')
      secrets = json.load(tokenFile)
      self.cToken = secrets["token"]
    except:
      print("ERROR: Could not read token from file: '{}'".format(secretsFile))
      raise
    finally:
      tokenFile.close()

    if not self.cToken:
      raise Exception("Discord API token could not be found")

cfgFile = 'cfg/config.json'

try:
  cfg = Config(cfgFile)
except Exception as e:
  print('ERROR: loading config file: {}: {}'.format(e, cfgFile))
  raise
except:
  print('ERROR: loading config file: {}'.format(cfgFile))
  raise