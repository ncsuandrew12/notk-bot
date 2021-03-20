# Local
from BotTesterProcess import BotTesterProcess
from BotTesterThread import BotTesterThread

class StartupTestProcess(BotTesterProcess):
  def testStartup(self):
    self.TestStartup()

class StartupTestThread(BotTesterThread):
  def testStartup(self):
    self.TestStartup()
