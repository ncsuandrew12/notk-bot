# Standard
import asyncio
import time
from datetime import datetime

# Local
import GuildBotManager
import Logging as log
import TestUtil as tu
from BotTesterThread import BotTesterThread
from TestConfig import testCfg

class StartupTestThread(BotTesterThread):

  def setUp(self):
    BotTesterThread.setUp(self)
    self.RunAndWaitForBot()

  def TestAmongUsCommandJoin(self, dObjs):
    preCommandTime = datetime.utcnow()
    ctx = GuildBotManager.notkBot.guildBots[self.client.client.guilds[0].id].GetContextStubbed()
    self.loop.run_until_complete(self.loop.create_task(GuildBotManager.notkBot.Command(ctx, testCfg.cCommandJoin)))
    self.client.FetchChannels()
    messages = self.client.FetchMessageHistoryAndFlatten(
      channel=self.client.channelsByName[testCfg.cBotChannelName],
      limit=None,
      after=preCommandTime,
      oldestFirst=True)
    # TODO Verify message response
    foundResponse = False
    for message in messages:
      log.Debug("Checking message: `@{}` @{}: {}".format(message.author.name, message.created_at, message.content))
      foundResponse = ((message.author.id == ctx.author.id) and
        (message.content ==
          "Hey `@among-us-test` players! {} is now among the Among Us players!".format(ctx.author.mention)))
      if (foundResponse):
        break
    self.assertTrue(foundResponse)
      # TODO Verify that member gained the role
      # TODO Verify that the bot responded with an announcement
      # TODO Verify that the user was sent a private message
    # TODO Test when a player adds themself without tagging themself
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
