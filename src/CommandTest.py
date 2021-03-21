# Standard
import asyncio
import time
from datetime import datetime

# Local
import GuildBotManager
import Logging as log
import TestUtil as tu
from BotTesterInProcess import BotTesterInProcess
from TestConfig import testCfg

class CommandTest(BotTesterInProcess):

  def setUp(self):
    BotTesterInProcess.setUp(self)
    self.RunAndWaitForBot()
    self.guildBot = self.GetGuildBot()

  def TestAmongUsCommandJoin(self, dObjs):
    users = []
    expectedUsersInRole = [self.guildBot.bot.user]
    expectedUserMessages = [self.guildBot.bot.user]
    self.TestAmongUsCommandJoinPermutation(dObjs, users, expectedUsersInRole, expectedUserMessages)
    expectedUserMessages = []
    self.TestAmongUsCommandJoinPermutation(dObjs, users, expectedUsersInRole, expectedUserMessages)

  def TestAmongUsCommandJoinPermutation(self, dObjs, users, expectedUsersInRole, expectedUserMessages):
    preCommandTime = datetime.utcnow()
    ctx = self.guildBot.GetContextStubbed()
    args = []
    expectedMessages = []
    for user in users:
      args.append(user.mention)
    actualExpectedUsersInRole = []
    self.loop.run_until_complete(self.loop.create_task(GuildBotManager.notkBot.Command(ctx, testCfg.cCommandJoin, *args)))
    log.Info("Testing that all expected role members are enrolled: {}: {}".format(
      self.guildBot.roleAmongUs.id,
      actualExpectedUsersInRole))
    for user in expectedUsersInRole:
      actualExpectedUsersInRole.append(self.loop.run_until_complete(self.guildBot.guild.fetch_member(user.id)))
    for user in actualExpectedUsersInRole:
      log.Info("Testing that {} is enrolled in {}:\n{}".format(user, self.guildBot.roleAmongUs.id, tu.GetIDDict(user.roles)))
      self.assertTrue(self.guildBot.roleAmongUs.id in tu.GetIDDict(user.roles))
    self.client.FetchChannels()
    for user in expectedUserMessages:
      expectedMessages.append([
        user,
        "Hey `@among-us-test` players! {} is now among the Among Us players!".format(
          self.loop.run_until_complete(self.guildBot.guild.fetch_member(user.id)).mention)])
    messages = self.client.FetchMessageHistoryAndFlatten(
      channel=self.client.channelsByName[testCfg.cBotChannelName],
      limit=None,
      after=preCommandTime,
      oldestFirst=True)
    log.Info("Testing that expected messages were sent: {}, {}".format(expectedMessages, messages))
    self.assertEquals(len(messages), len(expectedUserMessages))
    foundMessages = []
    for message in messages:
      log.Debug("Checking message: `@{}` @{}: {}".format(message.author.name, message.created_at, message.content))
      for expectedMessage in expectedMessages:
        if (message.author.id == expectedMessage[0].id) and (message.content == expectedMessage[1]):
          foundMessages.append(message.content)
    for expectedMessage in expectedMessages:
      if not expectedMessage[1] in foundMessages:
        self.fail()
        break
    # FUTURE Verify that the user was sent a private message?
    # TODO Test when a player adds another player
    # TODO Test when a player adds an invalid player
    # TODO Test when a player adds already-added players (self/others)
    # TODO Test all of the above for multiple other players of heterogenous statuses
    # TODO Test all of the above in an unrelated private channel
    # TODO Test all of the above in an unrelated public channel

  # TODO Break this into its own test class and split the sub-tests into their own tests
  def testCommands(self):
    dObjs = self.LocateDiscordObjects()
    self.TestAmongUsCommandJoin(dObjs)
    # self.TestAmongUsCommandLeave(dObjs)
    self.ShutdownBot()
