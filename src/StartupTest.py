# Local
from BotStandaloneTest import BotStandaloneTest
from BotInProcessTest import BotInProcessTest

# class StartupTestStandalone(BotStandaloneTest):
#   def testStartup(self):
#     self.bt.TestStartup()

class StartupTestInProcess(BotInProcessTest):
  def testStartup(self):
    self.bt.TestStartup()
