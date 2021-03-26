# Standard
import unittest as ut

# Local
from BotStandaloneTester import BotStandaloneTester

class BotStandaloneTest(ut.TestCase):

  def setUp(self):
    self.bt = BotStandaloneTester()
    self.bt.SetUpTester()

  def tearDown(self):
    self.bt.TearDownTester()
    self.bt = None
