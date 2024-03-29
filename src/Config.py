# Standard
import getpass
import json
import os

# Local
import Error

class Config:
  def __init__(self, configFilename):
    self.cUserBotDeveloper = None
    self.cUserBotDeveloperID = None
    self.cCommandJoin = "join"
    self.cCommandLeave = "leave"
    self.cCommandNewGame = "newgame"
    self.cExternalChanges = "EXTERNAL CHANGES"
    self.cReleaseNotesHeader = "Release Notes:"
    self.cRoleModPrefix = "mod"
    self.cRoleModSubstring = "moderator"
    self.cTestMode = False

    self.cUniversalSuffix = ""
    secretsFile = "cfg/secrets.json"
    self.cCommandPrefix="$"

    self.cDbHost = "localhost"
    self.cDbUser = getpass.getuser()
    self.cDbPort = 3306
    self.cDbName = "notkBot"

    with open(configFilename) as file:
      config = json.load(file)

    dbNameSuffix = ""
    for cfgKey in config:
      if cfgKey == "universalSuffix":
        self.cUniversalSuffix = config[cfgKey]
      elif cfgKey == "secretFile":
        secretsFile = "cfg/" + config[cfgKey]
      elif cfgKey == "commandPrefix":
        self.cCommandPrefix=config[cfgKey]
      elif cfgKey == "developer":
        for developerKey in config[cfgKey]:
          if developerKey == "discordUserID":
            self.cUserBotDeveloperID = config[cfgKey][developerKey]
      elif cfgKey == "database":
        databaseCfg = config[cfgKey]
        for dbKey in databaseCfg:
          if dbKey == "host":
            self.cDbHost = databaseCfg[dbKey]
          elif dbKey == "port":
            self.cDbPort = int(databaseCfg[dbKey])
          elif dbKey == "user":
            self.cDbUser = databaseCfg[dbKey]
          elif dbKey == "name":
            self.cDbName = databaseCfg[dbKey]
          elif dbKey == "nameSuffix":
            dbNameSuffix = databaseCfg[dbKey]
      elif cfgKey == "test":
        self.cTestMode = config[cfgKey]

    self.cDbName += dbNameSuffix

    self.cBotName = "notk-bot{}".format(self.cUniversalSuffix)

    self.cCommandRoot = "re" # Must match the @bot.commmand() function name
    self.cAUCommandRoot = "au"

    self.cAmongUsRoleName = "among-us{}".format(self.cUniversalSuffix)
    self.cAmongUsCodesChannelName = "among-us-codes"
    self.cBotChannelName = self.cBotName
    self.cCommandBase = "{}{}".format(self.cCommandPrefix, self.cCommandRoot)
    self.cAUCommandBase = "{} {}".format(self.cCommandBase, self.cAUCommandRoot)
    self.cLogChannelName = "{}-log".format(self.cBotChannelName)
    self.cInstructionalLine = "⚠ {} Instructions ⚠".format(self.cBotName)

    self.cAmongUsJoinRequestMessageText = "{} {}".format(self.cAUCommandBase, self.cCommandJoin)
    self.cAmongUsLeaveRequestMessageText = "{} {}".format(self.cAUCommandBase, self.cCommandLeave)
    self.cAmongUsSendGameNotificationText = \
      "Type `{} {} <room-code>` in any public channel to send a new game notification.".format(
        self.cAUCommandBase,
        self.cCommandNewGame)

    with open(secretsFile) as file:
      secrets = json.load(file)

    for cfgKey in secrets:
      if cfgKey == "token":
        self.cToken = secrets[cfgKey]
      elif cfgKey == "dbPassword":
        self.cDbPassword = secrets[cfgKey]
      elif (cfgKey == "testUser"):
        if self.cTestMode:
          for testUserKey in secrets[cfgKey]:
            if testUserKey == "token":
              self.cTestUserToken = secrets[cfgKey][testUserKey]

    if not self.cToken:
      raise Error.NotKException("Discord API token could not be found")

cfgFile = 'cfg/config.json'

try:
  cfg = Config(cfgFile)
except Exception as e:
  print('ERROR: loading config file: {}: {}'.format(e, cfgFile))
  raise
except:
  print('ERROR: loading config file: {}'.format(cfgFile))
  raise