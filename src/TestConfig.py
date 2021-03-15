# Modules

# notk-bot

from Config import cfg

class TestConfig:
  def __init__(self):
    self.cAmongUsRoleName = "among-us-test"
    self.cBotChannelName = "notk-bot-test"
    self.cLogChannelName = "notk-bot-test-log"
    self.cInstructionalLine = "⚠ notk-bot-test Instructions ⚠"
    self.cReleaseNotesHeader = "Release Notes:"
    self.cChannelNames = [ self.cBotChannelName, self.cLogChannelName ]
    self.cRoleNames = [ self.cAmongUsRoleName ]

testCfg = TestConfig()
