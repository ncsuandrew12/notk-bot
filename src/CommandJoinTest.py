# Standard
import time
from datetime import datetime

# Local
import TestUtil as tu
from CommandTest import CommandTest
from CommandTest import RoleRoll
from Logging import logger as log
from TestConfig import testCfg

class CommandJoinTest(CommandTest):

  def setUp(self):
    CommandTest.setUp(self)

  def tearDown(self):
    CommandTest.tearDown(self)

  def TestAmongUsCommandJoin(self, users, roleRoll, expectedJoined):
    preCommandTime = datetime.utcnow()
    self.RunAmongUsCommandJoin(users)
    self.VerifyAmongUsRole(roleRoll)
    self.bt.client.FetchChannels()
    allMessages = self.bt.client.FetchMessageHistoryAndFlatten(
      channel=self.bt.client.channelsByName[testCfg.cBotChannelName],
      limit=None,
      after=preCommandTime,
      oldestFirst=True)
    log.debug("allMessages: %s", allMessages)
    matchedMessages = []
    for message in allMessages:
      msgLogDescription = "{} `@{}` @{}: {}".format(message, message.author.name, message.created_at, message.content)
      if (message.author.id == self.bt.guildBot.bot.user.id) and (message.created_at >= preCommandTime):
        log.debug("Found matching message: %s", msgLogDescription)
        matchedMessages.append(message)
      else:
        log.debug("Ignoring non-matching message: %s", msgLogDescription)
    log.debug("matchedMessages: %s, expectedJoined: %s", matchedMessages, expectedJoined)
    self.assertEqual(len(matchedMessages), len(expectedJoined))
    self.bt.VerifyExpectedUserMessages(
      matchedMessages,
      expectedJoined,
      [],
      ["Hey `@{data.amongUsRole.name}` players! {data.user.mention} is now among the Among Us players!"])

  def TestAmongUsCommandJoinAllJoin(self, users):
    self.TestAmongUsCommandJoin(users, RoleRoll(users, []), users)

  def testAmongUsCommandJoinSelf(self):
    self.TestAmongUsCommandJoin([], RoleRoll([self.bt.guildBot.bot.user], []), [self.bt.guildBot.bot.user])

  def testAmongUsCommandJoinSelfTagged(self):
    self.TestAmongUsCommandJoinAllJoin([self.bt.guildBot.bot.user])

  def testAmongUsCommandJoinOther(self):
    self.TestAmongUsCommandJoinAllJoin([self.bt.otherMember])

  def testAmongUsCommandJoinSelfAndOther(self):
    self.TestAmongUsCommandJoinAllJoin([self.bt.guildBot.bot.user, self.bt.otherMember])

  def testAmongUsCommandJoinInvalid(self):
    self.TestAmongUsCommandJoin(["invalid"], RoleRoll([], []), [])

  def testAmongUsCommandJoinMixedValidity(self):
    self.TestAmongUsCommandJoin(
      [self.bt.guildBot.bot.user, "invalid", self.bt.otherMember],
      RoleRoll([self.bt.guildBot.bot.user, self.bt.otherMember], []),
      [self.bt.guildBot.bot.user, self.bt.otherMember])

  def testAmongUsCommandJoinSelfAndOtherAlreadyBoth(self):
    self.TestAmongUsCommandJoinAllJoin([self.bt.guildBot.bot.user, self.bt.otherMember])
    self.TestAmongUsCommandJoin(
      [self.bt.guildBot.bot.user, self.bt.otherMember],
      RoleRoll([self.bt.guildBot.bot.user, self.bt.otherMember], []),
      [])

  def testAmongUsCommandJoinSelfAndOtherMixedAlready(self):
    self.TestAmongUsCommandJoinAllJoin([self.bt.guildBot.bot.user])
    self.TestAmongUsCommandJoin(
      [self.bt.guildBot.bot.user, self.bt.otherMember],
      RoleRoll([self.bt.guildBot.bot.user, self.bt.otherMember], []),
      [self.bt.otherMember])

  def testAmongUsCommandJoinSelfAndOtherMixedValidity(self):
    self.TestAmongUsCommandJoin([], RoleRoll([self.bt.guildBot.bot.user], []), [self.bt.guildBot.bot.user])
    self.TestAmongUsCommandJoin(
      [self.bt.guildBot.bot.user, "invalid", self.bt.otherMember],
      RoleRoll([self.bt.guildBot.bot.user, self.bt.otherMember], []),
      [self.bt.otherMember])
