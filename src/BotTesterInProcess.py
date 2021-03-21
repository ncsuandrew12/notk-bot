# Standard
import asyncio
import time
from threading import Thread

# Local
import Error
import Logging as log
import TestUtil as tu

from BotTester import BotTester
import GuildBotManager

class BotTesterInProcess(BotTester):

  def LaunchBot(self):
    GuildBotManager.notkBot.Run()
    return GuildBotManager.notkBot

  def TerminateBot(self):
    self.bot.Shutdown()
