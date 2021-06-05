# Standard
import time
from datetime import datetime

# Local
import TestUtil as tu
from CommandTest import CommandTest
from LoggingTest import logger as log
from TestConfig import testCfg

class CommandNewGameTest(CommandTest):

  def setUp(self):
    CommandTest.setUp(self)

  def tearDown(self):
    CommandTest.tearDown(self)

  def TestAmongUsCommandNewGame(self, gameCodeValid, gameCode):
    preCommandTime = datetime.utcnow()
    self.RunAmongUsCommandNewGame(gameCode)
    self.bt.client.FetchChannels()
    recentMessages = self.bt.client.FetchMessageHistoryAndFlatten(
      channel=self.bt.client.channelsByName[testCfg.cAmongUsCodesChannelName],
      limit=None,
      after=preCommandTime,
      oldestFirst=True)
    log.debug("recentMessages: %s", recentMessages)
    matchedMessages = []
    for message in recentMessages:
      msgLogDescription = "{} `@{}` @{}: {}".format(message, message.author.name, message.created_at, message.content)
      log.debug("Checking message: %s", msgLogDescription)
      if (message.author.id == self.bt.guildBot.bot.user.id) and (message.created_at >= preCommandTime):
        log.debug("Found matching message: %s", msgLogDescription)
        matchedMessages.append(message)
      else:
        log.debug("Ignoring non-matching message: %s", msgLogDescription)
    expectedMessages = []
    if gameCodeValid:
      expectedMessages.append("Attention {data.amongUsRole.mention}! New game code: `{data.gameCode}`. Type `{data.amongUsLeaveRequestMessageText}` if you no longer want to receive these notifications. {data.amongUsSendGameNotificationText}")
    log.debug("matchedMessages: %s, expectedMessages: %s", matchedMessages, expectedMessages)
    self.assertEqual(len(matchedMessages), len(expectedMessages))
    self.bt.VerifyExpectedNewGameMessages(matchedMessages, expectedMessages, gameCode if gameCode == None else gameCode.upper())

  def testAmongUsCommandNewGameValid(self):
    self.TestAmongUsCommandNewGame(True, "GOLLUM")
    self.TestAmongUsCommandNewGame(True, "Pippin")
    
  def testAmongUsCommandNewGameInvalid(self):
    self.TestAmongUsCommandNewGame(False, None)
    self.TestAmongUsCommandNewGame(False, "")
    self.TestAmongUsCommandNewGame(False, "Merry")
    self.TestAmongUsCommandNewGame(False, "Gandalf")
    self.TestAmongUsCommandNewGame(False, "Numba1")
    self.TestAmongUsCommandNewGame(False, "$Cash$")
    self.TestAmongUsCommandNewGame(False, "@#(%)!")
