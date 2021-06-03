# Standard
import time
from datetime import datetime

# Local
import TestUtil as tu
from CommandTest import CommandTest
from CommandTest import RoleRoll
from Logging import logger as log
from TestConfig import testCfg

class CommandLeaveTest(CommandTest):

  def setUp(self):
    CommandTest.setUp(self)
    roleRoll = RoleRoll([self.bt.guildBot.bot.user, self.bt.otherMember], [])
    self.RunAmongUsCommandJoin(roleRoll.enrolled)
    self.VerifyAmongUsRole(roleRoll)

  def tearDown(self):
    CommandTest.tearDown(self)

  def TestAmongUsCommandLeave(self, users, roleRoll, expectedLeft):
    preCommandTime = datetime.utcnow()
    self.RunAmongUsCommandLeave(users)
    # Make sure the users who left are included in the notEnrolled list.
    for user in expectedLeft:
      if not user in roleRoll.notEnrolled:
        roleRoll.notEnrolled.append(user)
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
    log.debug("matchedMessages: %s, expectedLeft: %s", matchedMessages, expectedLeft)
    self.assertEqual(len(matchedMessages), len(expectedLeft))
    self.bt.VerifyExpectedUserMessages(
      matchedMessages,
      expectedLeft,
      [],
      ["{data.user.mention} is now Among The Hidden."])

  def TestAmongUsCommandLeaveAllLeave(self, users):
    # TODO Populate 'enrolled' with this pseudocode: allUsers - users
    self.TestAmongUsCommandLeave(users, RoleRoll([], users), users)

  def testAmongUsCommandLeaveSelf(self):
    self.TestAmongUsCommandLeave([], RoleRoll([self.bt.otherMember], []), [self.bt.guildBot.bot.user])

  def testAmongUsCommandLeaveSelfTagged(self):
    self.TestAmongUsCommandLeaveAllLeave([self.bt.guildBot.bot.user])

  def testAmongUsCommandLeaveOther(self):
    self.TestAmongUsCommandLeaveAllLeave([self.bt.otherMember])

  def testAmongUsCommandLeaveSelfAndOther(self):
    self.TestAmongUsCommandLeaveAllLeave([self.bt.guildBot.bot.user, self.bt.otherMember])

  def testAmongUsCommandLeaveInvalid(self):
    self.TestAmongUsCommandLeave(["invalid"], RoleRoll([], []), [])

  def testAmongUsCommandLeaveMixedValidity(self):
    self.TestAmongUsCommandLeave(
      [self.bt.guildBot.bot.user, "invalid", self.bt.otherMember],
      RoleRoll([], [self.bt.guildBot.bot.user, self.bt.otherMember]),
      [self.bt.guildBot.bot.user, self.bt.otherMember])

  def testAmongUsCommandLeaveSelfAndOtherAlreadyBoth(self):
    self.TestAmongUsCommandLeaveAllLeave([self.bt.guildBot.bot.user, self.bt.otherMember])
    self.TestAmongUsCommandLeave(
      [self.bt.guildBot.bot.user, self.bt.otherMember],
      RoleRoll([], [self.bt.guildBot.bot.user, self.bt.otherMember]),
      [])

  def testAmongUsCommandLeaveSelfAndOtherMixedAlready(self):
    self.TestAmongUsCommandLeaveAllLeave([self.bt.guildBot.bot.user])
    self.TestAmongUsCommandLeave(
      [self.bt.guildBot.bot.user, self.bt.otherMember],
      RoleRoll([], [self.bt.guildBot.bot.user, self.bt.otherMember]),
      [self.bt.otherMember])

  def testAmongUsCommandLeaveSelfAndOtherMixedValidity(self):
    self.TestAmongUsCommandLeave([], RoleRoll([], [self.bt.guildBot.bot.user]), [self.bt.guildBot.bot.user])
    self.TestAmongUsCommandLeave(
      [self.bt.guildBot.bot.user, "invalid", self.bt.otherMember],
      RoleRoll([], [self.bt.guildBot.bot.user, self.bt.otherMember]),
      [self.bt.otherMember])
