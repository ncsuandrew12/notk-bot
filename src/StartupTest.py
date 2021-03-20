# Local
from BotTesterProcess import BotTesterProcess

class StartupTest(BotTesterProcess):

  def testStartup(self):
    self.TestVirgin()
    self.TestStandardRestart()
    self.TestMissingChannels()
    self.TestMissingRoles()
    self.TestPreExistingChannels()
