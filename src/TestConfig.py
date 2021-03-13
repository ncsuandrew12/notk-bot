# Modules

# notk-bot

from Config import cfg

class TestConfig:
  def __init__(self):
    self.cAmongUsRoleName = "among-us{}".format(cfg.cUniversalSuffix)
    self.cBotChannelName = "notk-bot{}".format(cfg.cUniversalSuffix)
    self.cLogChannelName = "notk-bot{}-log".format(cfg.cUniversalSuffix)
    self.cChannelNames = [ self.cBotChannelName, self.cLogChannelName ]
    self.cRoleNames = [ self.cAmongUsRoleName ]

testCfg = TestConfig()
