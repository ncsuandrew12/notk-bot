# Standard
import unittest as ut

# Local
from BotInProcessTester import BotInProcessTester

class BotInProcessTest(ut.TestCase):

  def setUp(self):
    self.bt = BotInProcessTester()
    self.bt.SetUpTester()

  def tearDown(self):
    self.bt.TearDownTester()
    self.bt = None
