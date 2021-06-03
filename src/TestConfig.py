# Local
from Config import cfg

class TestConfig:
  def __init__(self):
    self.cCommandJoin = "join"
    self.cCommandLeave = "leave"
    self.cCommandNewGame = "newgame"
    self.cCommandPrefix = "$"
    self.cCommandRoot = "au"
    # self.cExternalChanges = "EXTERNAL CHANGES"
    self.cReleaseNotesHeader = "Release Notes:"
    # self.cRoleModPrefix = "mod"
    # self.cRoleModSubstring = "moderator"

    self.cAmongUsRoleName = "among-us-test"
    self.cAmongUsCodesChannelName = "among-us-codes"
    self.cBotChannelName = "notk-bot-test"
    self.cLogChannelName = "notk-bot-test-log"
    self.cTestChannelName = "notk-bot-test-public"
    self.cInstructionalLine = "⚠ notk-bot-test Instructions ⚠"
    self.cTestChannelNames = [ self.cTestChannelName ]
    self.cChannelNames = [ self.cAmongUsCodesChannelName, self.cBotChannelName, self.cLogChannelName ]
    self.cRoleNames = [ self.cAmongUsRoleName ]

testCfg = TestConfig()
