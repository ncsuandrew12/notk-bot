# Standard
import asyncio
import time
from datetime import datetime

# Local
import GuildBotManager
import Logging as log
import TestUtil as tu
from BotTesterInProcess import BotTesterInProcess
from CommandTest import CommandTest
from TestConfig import testCfg

class CommandJoinTest(CommandTest):

  def setUp(self):
    CommandTest.setUp(self)
    self.bt.client.RemoveAllMembersFromRole(self.bt.guildBot.roleAmongUs)

  def tearDown(self):
    self.bt.client.RemoveAllMembersFromRole(self.bt.guildBot.roleAmongUs)
    CommandTest.tearDown(self)

  def TestAmongUsCommandJoinAllJoin(self, users):
    self.TestAmongUsCommandJoin(users, users, users)

  def TestAmongUsCommandJoin(
    self,
    users,
    expectedUsersInRole,
    expectedJoined):
    preCommandTime = datetime.utcnow()
    ctx = self.bt.guildBot.GetContextStubbed()
    args = []
    for user in users:
      if user == "invalid":
        # Member parameters must be tagged. Therefore, a simple name is invalid.
        args.append(self.bt.guildBot.bot.user.name)
      else:
        args.append(user.mention)
    self.bt.loop.run_until_complete(self.bt.loop.create_task(GuildBotManager.notkBot.Command(ctx, testCfg.cCommandJoin, *args)))
    actualExpectedUsersInRole = []
    for user in expectedUsersInRole:
      actualExpectedUsersInRole.append(self.bt.loop.run_until_complete(self.bt.guildBot.guild.fetch_member(user.id)))
    log.Info("Testing that all expected role members were enrolled: {}: {}".format(
      self.bt.guildBot.roleAmongUs.id,
      actualExpectedUsersInRole))
    for user in actualExpectedUsersInRole:
      userRoles = tu.GetIDDict(user.roles)
      log.Info("Testing that {} is enrolled in {}:\n{}".format(user, self.bt.guildBot.roleAmongUs.id, userRoles))
      self.assertTrue(self.bt.guildBot.roleAmongUs.id in userRoles)
    self.bt.client.FetchChannels()
    messagesMain2 = self.bt.client.FetchMessageHistoryAndFlatten(
      channel=self.bt.client.channelsByName[testCfg.cBotChannelName],
      limit=None,
      after=preCommandTime,
      oldestFirst=True)
    log.Debug("messagesMain2: {}".format(messagesMain2))
    messagesMain = []
    for message in messagesMain2:
      msgLogDescription = "{} `@{}` @{}: {}".format(message, message.author.name, message.created_at, message.content)
      if (message.author.id == self.bt.guildBot.bot.user.id) and (message.created_at >= preCommandTime):
        log.Debug("Found matching message: {}".format(msgLogDescription))
        messagesMain.append(message)
      else:
        log.Debug("Ignoring non-matching message: {}".format(msgLogDescription))
    log.Debug("messagesMain: {}, expectedJoined: {}".format(messagesMain, expectedJoined))
    self.assertEqual(len(messagesMain), len(expectedJoined))
    messagesLog2 = self.bt.client.FetchMessageHistoryAndFlatten(
      channel=self.bt.client.channelsByName[testCfg.cLogChannelName],
      limit=None,
      after=preCommandTime,
      oldestFirst=True)
    self.bt.VerifyExpectedUserMessages(
      messagesMain,
      expectedJoined,
      [],
      ["Hey `@{data.amongUsRoleName}` players! {data.user.mention} is now among the Among Us players!"])
    # FUTURE Verify users' private messages?

  def testAmongUsCommandJoinSelf(self):
    self.TestAmongUsCommandJoin([], [self.bt.guildBot.bot.user], [self.bt.guildBot.bot.user])

  def testAmongUsCommandJoinSelfTagged(self):
    self.TestAmongUsCommandJoinAllJoin([self.bt.guildBot.bot.user])

  def testAmongUsCommandJoinOther(self):
    self.TestAmongUsCommandJoinAllJoin([self.bt.otherMember])

  def testAmongUsCommandJoinSelfAndOther(self):
    self.TestAmongUsCommandJoinAllJoin([self.bt.guildBot.bot.user, self.bt.otherMember])

  def testAmongUsCommandJoinInvalid(self):
    self.TestAmongUsCommandJoin(["invalid"], [], [])

  def testAmongUsCommandJoinMixedValidity(self):
    self.TestAmongUsCommandJoin(
      [self.bt.guildBot.bot.user, "invalid", self.bt.otherMember],
      [self.bt.guildBot.bot.user, self.bt.otherMember],
      [self.bt.guildBot.bot.user, self.bt.otherMember])

  def testAmongUsCommandJoinSelfAndOtherAlreadyBoth(self):
    self.TestAmongUsCommandJoinAllJoin([self.bt.guildBot.bot.user, self.bt.otherMember])
    self.TestAmongUsCommandJoin(
      [self.bt.guildBot.bot.user, self.bt.otherMember],
      [self.bt.guildBot.bot.user, self.bt.otherMember],
      [])

  def testAmongUsCommandJoinSelfAndOtherMixedAlready(self):
    self.TestAmongUsCommandJoinAllJoin([self.bt.guildBot.bot.user])
    self.TestAmongUsCommandJoin(
      [self.bt.guildBot.bot.user, self.bt.otherMember],
      [self.bt.guildBot.bot.user, self.bt.otherMember],
      [self.bt.otherMember])

  def testAmongUsCommandJoinSelfAndOtherMixedValidity(self):
    self.TestAmongUsCommandJoin([], [self.bt.guildBot.bot.user], [self.bt.guildBot.bot.user])
    self.TestAmongUsCommandJoin(
      [self.bt.guildBot.bot.user, "invalid", self.bt.otherMember],
      [self.bt.guildBot.bot.user, self.bt.otherMember],
      [self.bt.otherMember])
