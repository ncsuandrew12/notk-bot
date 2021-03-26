# Standard

# Local
from BotInProcessTest import BotInProcessTest
from BotInProcessTester import BotInProcessTester

class CommandTest(BotInProcessTest):

  bt = None

  def setUpClass():
    BotInProcessTester.bt = BotInProcessTester()
    BotInProcessTester.bt.SetUpTester()
    BotInProcessTester.bt.RunAndWaitForBot()

  def tearDownClass():
    BotInProcessTester.bt.TearDownTester()
    BotInProcessTester.bt = None

  def setUp(self):
    if not self.bt:
      self.bt = BotInProcessTester.bt

  def tearDown(self):
    pass
