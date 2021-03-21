# Local
from BotTesterStandalone import BotTesterStandalone
from BotTesterInProcess import BotTesterInProcess

class StartupTestStandalone(BotTesterStandalone):
  def testStartup(self):
    self.TestStartup()

class StartupTestInProcess(BotTesterInProcess):
  def testStartup(self):
    self.TestStartup()
