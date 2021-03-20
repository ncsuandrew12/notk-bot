# Standard
import asyncio
import time
import unittest as ut

from datetime import datetime

# Local
import Error
import Logging as log
import TestClient
import TestUtil as tu
import Util

from TestConfig import testCfg

class BotTester(ut.TestCase):

  def setUp(self):
    self.bot = None
    self.botLaunchTime = None
    self.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(self.loop)
    self.client = TestClient.TestClient(self.loop)
    self.client.database.Connect()
    self.client.database.Clear()
    self.client.Run()
    self.client.WaitUntilReady()
    self.client.ResetGuild()

  def tearDown(self):
    try:
      self.TerminateBot()
    except:
      # TODO Log a warning if-and-only-if the bot wasn't already killed by the test
      pass
    if self.DidTestPass():
      self.client.database.Clear()
      self.client.ResetGuild()
      self.client.Shutdown()
    self.loop.stop()

  def TerminateBot(self):
    assert False

  def DidTestPass(self):
    if hasattr(self, '_outcome'):  # Python 3.4+
        result = self.defaultTestResult()  # These two methods have no side effects
        self._feedErrorsToResult(result, self._outcome.errors)
    else:  # Python 2.7, 3.0 - 3.3
        result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
    error = self.TestIssuesToReason(result.errors)
    failure = self.TestIssuesToReason(result.failures)
    return not error and not failure

  def TestIssuesToReason(self, issuesList):
      if issuesList and issuesList[-1][0] is self:
          return issuesList[-1][1]

  def RunAndWaitForBot(self):
    self.RunBot()
    self.WaitForBot()

  def RunBot(self):
    assert not self.bot
    self.botLaunchTime = datetime.utcnow()
    self.bot = self.LaunchBot()

  def LaunchBot(self):
    assert False

  def WaitForBot(self):
    time.sleep(9)
    waited = 9
    while True:
      if waited >= 30:
        Error.Err("Timed out waiting for {}'s bot to come online.".format(self.client.client.guilds[0].name))
      try:
        if self.client.database.GetBotStatus(self.client.client.guilds[0].id) == "RUNNING":
          break
      except Exception as e:
        log.Debug("{}".format(e))
      log.Info("Waiting for bot to come online")
      time.sleep(1)
      waited+= 1

  def ShutdownBot(self):
    if self.bot:
      self.TerminateBot()
      self.WaitForBotShutdown()
      self.bot = None

  def WaitForBotShutdown(self):
    waited = 0
    while self.client.database.GetBotStatus(self.client.client.guilds[0].id) != "OFFLINE":
      if waited > 20:
        Error.Err("Timed out while waiting for {}'s bot to shutdown.".format(self.client.client.guilds[0].name))
      time.sleep(1)
      waited += 1

  def LocateDiscordObjects(self):
    log.Debug("Locating Discord objects.")
    container = tu.Container()
    container.instructionalMessage = None
    container.releaseNotesMessage = None
    container.rolesNameDict = tu.GetNameDict(self.client.FetchRoles())
    container.channelsNameDict = tu.GetNameDict(self.client.FetchChannels(), testCfg.cChannelNames)
    if testCfg.cBotChannelName in container.channelsNameDict:
      messages = self.client.FetchMessageHistoryAndFlatten(
        channel=container.channelsNameDict[testCfg.cBotChannelName],
        limit=None,
        oldestFirst=True)
      for message in messages:
        if message.content.startswith(testCfg.cReleaseNotesHeader):
          container.releaseNotesMessage = message
        if testCfg.cInstructionalLine in message.content.partition('\n')[0]:
          container.instructionalMessage = message
    return container

  def StartupVerify(self):
    self.RunAndWaitForBot()
    self.VerifyStartup()

  def StartupVerifyShutdown(self):
    self.StartupVerify()
    self.ShutdownBot()

  def VerifyClean(self):
    log.Info("Verifying clean state")
    self.assertTrue(all(name not in tu.GetNameDict(self.client.FetchRoles()) for name in testCfg.cRoleNames))
    self.assertTrue(all(name not in tu.GetNameDict(self.client.FetchChannels()) for name in testCfg.cChannelNames))

  def VerifyStartup(self):
    dObjs = self.LocateDiscordObjects()
    self.VerifyAllRoles(dObjs.rolesNameDict)
    self.VerifyAllChannels(dObjs)

  def VerifyAllRoles(self, rolesNameDict):
    log.Info("Verifying existence of all roles")
    self.assertTrue(all(name in rolesNameDict for name in testCfg.cRoleNames))

  def VerifyAllChannels(self, dObjs):
    log.Info("Verifying existence of all channels")
    self.assertTrue(all(name in dObjs.channelsNameDict for name in testCfg.cChannelNames))
    self.VerifyAllChannelsContent(dObjs)

  def VerifyAllChannelsContent(self, dObjs):
    log.Info("Verifying channels' content.")
    self.assertTrue(dObjs.releaseNotesMessage)
    self.assertTrue(dObjs.instructionalMessage)
    for channelName in dObjs.channelsNameDict:
      channel = dObjs.channelsNameDict[channelName]
      if channel.name == testCfg.cBotChannelName:
        # TODO Verify release notes message content
        expectedInstructionMessageContent = """⚠ notk-bot-test Instructions ⚠
Type `{cmdPrefix} {cmdJoin}` in any public channel to be notified about NOTK Among Us game sessions.
Type `{cmdPrefix} {cmdLeave}` in any public channel if you no longer want to be notified.
Type `{cmdPrefix} {cmdNewGame} <room-code>` in any public channel to send a new game notification.
Tag the `among-us-test` role to ping all Among Us players like so: <@&{amongUsRoleID}>
I recommend muting the <#{logChannelID}> channel; it is only for logging purposes and will be very noisy.""".format(
          cmdPrefix=testCfg.cCommandPrefix + testCfg.cCommandRoot,
          cmdJoin=testCfg.cCommandJoin,
          cmdLeave=testCfg.cCommandLeave,
          cmdNewGame=testCfg.cCommandNewGame,
          amongUsRoleID=dObjs.rolesNameDict[testCfg.cAmongUsRoleName].id,
          logChannelID=dObjs.channelsNameDict[testCfg.cLogChannelName].id)
        if dObjs.instructionalMessage.content != expectedInstructionMessageContent:
          log.Info(
            "Instructional message content mismatch:\n\"\"\"{}\"\"\"\n\"\"\"{}\"\"\"".format(
              dObjs.instructionalMessage.content,
              expectedInstructionMessageContent))
        self.assertEqual(dObjs.instructionalMessage.content, expectedInstructionMessageContent)
      if channelName == testCfg.cLogChannelName:
        log.Info("Verifying `#{}` received messages during latest startup.".format(channelName))
        messages = self.client.FetchMessageHistoryAndFlatten(channel=channel, limit=1, after=self.botLaunchTime)
        self.assertGreater(len(messages), 0)
        # TODO Verify the content of the main channel's messages.
        # TODO Verify pinned messages

  def VerifyStandardRestart(self, oldObjs):
    self.VerifyStartup()
    self.VerifyOldRolesSurvivedRestart(oldObjs.rolesNameDict)
    self.VerifyOldChannelsSurvivedRestart(oldObjs)

  def VerifyOldRolesSurvivedRestart(self, oldRoles):
    log.Info("Verifying roles survived the restart.")
    self.assertTrue(oldRoles[roleName].id in tu.GetIDDict(self.client.FetchRoles()) for roleName in oldRoles)
  
  def VerifyOldChannelsSurvivedRestart(self, oldObjs):
    log.Info("Verifying channels survived the restart.")
    self.assertTrue(
      oldObjs.channelsNameDict[channelName].id in tu.GetIDDict(self.client.FetchChannels()) \
        for channelName in oldObjs.channelsNameDict)
    self.VerifyOldChannelsContentSurvivedRestart(oldObjs)

  def VerifyOldChannelsContentSurvivedRestart(self, oldObjs):
    log.Info("Verifying channels' content.")
    for channelName in testCfg.cChannelNames:
      log.Info("Verifying `#{}`. ({})".format(channelName, self.botLaunchTime))
      assert channelName in oldObjs.channelsNameDict
      channel = oldObjs.channelsNameDict[channelName]
      messages = self.client.FetchMessageHistoryAndFlatten(channel=channel, limit=1, after=self.botLaunchTime)
      expectedNewMessageCount = 0
      if channel.name == testCfg.cLogChannelName:
        expectedNewMessageCount = 1
      if len(messages) != expectedNewMessageCount:
        log.Warn("Unexpected message count: {} != {}".format(len(messages), expectedNewMessageCount))
        for message in messages:
          log.Warn("Message: {}: {}".format(message.created_at, message.content))
      assert len(messages) == expectedNewMessageCount
      # TODO Fully verify the release notes message(s)

  def TestStartup(self):
    self.TestVirgin()
    self.TestStandardRestart()
    self.TestMissingChannels()
    self.TestMissingRoles()
    self.TestPreExistingChannels()

  def TestVirgin(self):
    log.Info("Testing virgin startup")
    self.VerifyClean()
    self.StartupVerifyShutdown()

  def TestStandardRestart(self):
    preRestartDiscordObjects = self.LocateDiscordObjects()
    self.RunAndWaitForBot()
    self.VerifyStandardRestart(preRestartDiscordObjects)
    self.ShutdownBot()

  def TestMissingChannels(self):
    for channelName in testCfg.cChannelNames:
      log.Info("Testing startup with missing `#{}`".format(channelName))
      self.client.DeleteChannel(channelName)
      self.StartupVerifyShutdown()

  def TestMissingRoles(self):
    for roleName in [ testCfg.cAmongUsRoleName ]:
      log.Info("Testing startup with missing `@{}`".format(roleName))
      self.client.DeleteRole(roleName)
      self.StartupVerifyShutdown()

  def TestPreExistingChannels(self):
    log.Info("Testing startup with existing channels")
    channels = {}
    oldMessages = {}
    tasks = []
    for channel in self.client.client.guilds[0].channels:
      if channel.name in testCfg.cChannelNames:
        channels[channel.id] = channel
        tasks.append(self.TestPreExistingChannel(oldMessages, channel))
    Util.WaitForTasks(self.loop, tasks)
    log.Info("Verifying that the expected channels were found")
    self.assertEqual(len(testCfg.cChannelNames), len(channels))
    self.assertEqual(len(testCfg.cChannelNames), len(oldMessages))
    log.Info("Starting bot")
    self.StartupVerify()
    log.Info("Verifying that the pre-existing channels still exist")
    self.assertTrue(all(channelID in tu.GetIDDict(self.client.FetchChannels()) for channelID in channels))
    log.Info("Verifying that the pre-existing messages still exist")
    for channelID in channels:
      log.Info("Verifying that `#{}`'s messages were preserved".format(channels[channelID].name))
      self.loop.run_until_complete(channels[channelID].fetch_message(oldMessages[channelID].id))
      # FUTURE Verify more messages
      # Reaching here means the message was preserved
    self.ShutdownBot()

  async def TestPreExistingChannel(self, oldMessages, channel):
    oldMessages[channel.id] = await channel.send(content="test message")

  def TestPreExistingRoles(self):
    log.Info("Testing startup with existing channels")
    roles = {}
    oldMembers = {}
    addedMembers = {}
    try:
      for role in self.client.client.guilds[0].roles:
        if role.name in testCfg.cRoleNames:
          roles[role.id] = role
          # Ensure that the role has at least one member aside from the bot
          if len(role.members) < 2:
            for member in self.client.client.guilds[0].members:
              if member.id != role.members[0].id:
                self.loop.run_until_complete(
                  member.add_roles(
                    role,
                    reason="Need 1+ non-bot member of `@{}` for testing purposes; adding `@{}`".format(
                      role.name,
                      member.name)))
                addedMembers[role.id] = member
                break
          oldMembers[role.id] = role.members
          self.assertGreater(len(role.members), 1)
      log.Info("Verifying that the expected roles were found")
      self.assertEqual(len(testCfg.cRoleNames), len(roles))
      self.assertEqual(len(testCfg.cRoleNames), len(oldMembers))
      log.Info("Starting bot")
      self.StartupVerify()
      log.Info("Verifying that the pre-existing roles still exist")
      self.assertTrue(all(roleID in tu.GetIDDict(self.client.FetchRoles()) for roleID in roles))
      log.Info("Verifying that the pre-existing role members are still role members")
      log.Info("Testing that all of `@{}`'s members were preserved".format(role.name))
      self.assertTrue(all(member.id in tu.GetIDDict(role.members) for member in oldMembers[role.id] for role in roles))
      self.ShutdownBot()
    finally:
      try:
        for roleID in addedMembers:
          self.client.RemoveMemberRole(
            member=addedMembers[roleID],
            role=roles[roleID],
            reason="Cleanup: removing `@{}` from `@{}`".format(addedMembers[roleID].name, roles[roleID].name))
      except Exception as e:
        log.Warn("Error during cleanup: {}".format(e))
      except:
        log.Warn("Error during cleanup.")
