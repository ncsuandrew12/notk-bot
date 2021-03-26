# Standard
import asyncio
import time
import unittest as ut
from abc import ABCMeta, abstractmethod
from datetime import datetime

# Local
import Error
import GuildBotManager
import Logging as log
import TestClient
import TestUtil as tu
import Util
from TestConfig import testCfg

class BotTester(ut.TestCase, metaclass=ABCMeta):

  guild = None
  guildBot = None
  otherMember = None
  user = None

  def SetUpTester(self):
    self.bot = None
    self.botLaunchTime = None
    try:
      self.loop = asyncio.get_event_loop()
    except:
      self.loop = asyncio.new_event_loop()
      asyncio.set_event_loop(self.loop)
    self.client = TestClient.TestClient(self.loop)
    self.client.database.Connect()
    self.client.database.Clear()
    self.client.Run()
    self.client.WaitUntilReady()
    self.guild = self.client.client.guilds[0]
    self.client.ResetGuild()
    self.client.Setup()

  def TearDownTester(self):
    try:
      self.TerminateBot()
    except:
      # TODO Log a warning if-and-only-if the bot wasn't already killed by the test
      pass
    self.client.database.Clear()
    self.client.ResetGuild()
    self.client.Shutdown()

  @abstractmethod
  def TerminateBot(self):
    pass

  def RunAndWaitForBot(self):
    self.RunBot()
    self.WaitForBot()
    self.otherMember = None
    for member in self.loop.run_until_complete(self.guild.fetch_members().flatten()):
      if not member.id == self.client.client.user.id and member.bot: # Avoid tagging/messaging actual users.
        self.otherMember = member
    assert bool(self.otherMember)

  def RunBot(self):
    assert not self.bot
    self.botLaunchTime = datetime.utcnow()
    self.bot = self.LaunchBot()

  @abstractmethod
  def LaunchBot(self):
    pass

  def WaitForBot(self):
    time.sleep(5)
    waited = 5
    while True:
      if waited >= 30:
        Error.Err("Timed out waiting for {}'s bot to come online.".format(self.guild.name))
      try:
        if self.client.database.GetBotStatus(self.guild.id) == "RUNNING":
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
    while self.client.database.GetBotStatus(self.guild.id) != "OFFLINE":
      if waited > 20:
        Error.Err("Timed out while waiting for {}'s bot to shutdown.".format(self.guild.name))
      time.sleep(1)
      waited += 1

  def LocateDiscordObjects(self):
    log.Debug("Locating Discord objects.")
    container = tu.Container()
    container.instructionalMessage = None
    container.releaseNotesMessage = None
    self.client.FetchRoles()
    container.rolesByName = self.client.rolesByName
    self.client.FetchChannels()
    container.channelsByName = self.client.channelsByName
    if testCfg.cBotChannelName in container.channelsByName:
      messages = self.client.FetchMessageHistoryAndFlatten(
        channel=container.channelsByName[testCfg.cBotChannelName],
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
    self.client.FetchChannels()
    self.assertTrue(all(name not in self.client.channelsByID for name in testCfg.cRoleNames))
    self.assertTrue(all(name not in self.client.channelsByName for name in testCfg.cChannelNames))

  def VerifyStartup(self):
    dObjs = self.LocateDiscordObjects()
    self.VerifyAllRoles(dObjs.rolesByName)
    self.VerifyAllChannels(dObjs)

  def VerifyAllRoles(self, rolesByName):
    log.Info("Verifying existence of all roles")
    self.assertTrue(all(name in rolesByName for name in testCfg.cRoleNames))

  def VerifyAllChannels(self, dObjs):
    log.Info("Verifying existence of all channels")
    self.assertTrue(all(name in dObjs.channelsByName for name in testCfg.cChannelNames))
    self.VerifyAllChannelsContent(dObjs)

  def VerifyAllChannelsContent(self, dObjs):
    log.Info("Verifying channels' content.")
    self.assertTrue(dObjs.releaseNotesMessage)
    self.assertTrue(dObjs.instructionalMessage)
    for channelName in dObjs.channelsByName:
      channel = dObjs.channelsByName[channelName]
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
          amongUsRoleID=dObjs.rolesByName[testCfg.cAmongUsRoleName].id,
          logChannelID=dObjs.channelsByName[testCfg.cLogChannelName].id)
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
    self.VerifyOldRolesSurvivedRestart(oldObjs.rolesByName)
    self.VerifyOldChannelsSurvivedRestart(oldObjs)

  def VerifyOldRolesSurvivedRestart(self, oldRoles):
    log.Info("Verifying roles survived the restart.")
    self.client.FetchRoles()
    self.assertTrue(oldRoles[roleName].id in self.client.rolesByID for roleName in oldRoles)
  
  def VerifyOldChannelsSurvivedRestart(self, oldObjs):
    log.Info("Verifying channels survived the restart.")
    self.client.FetchChannels()
    self.assertTrue(
      oldObjs.channelsByName[channelName].id in self.client.channelsByName
        for channelName in oldObjs.channelsByName)
    self.VerifyOldChannelsContentSurvivedRestart(oldObjs)

  def VerifyOldChannelsContentSurvivedRestart(self, oldObjs):
    log.Info("Verifying channels' content.")
    for channelName in testCfg.cChannelNames:
      log.Info("Verifying `#{}`. ({})".format(channelName, self.botLaunchTime))
      self.assertTrue(channelName in oldObjs.channelsByName)
      channel = oldObjs.channelsByName[channelName]
      messages = self.client.FetchMessageHistoryAndFlatten(channel=channel, limit=1, after=self.botLaunchTime)
      expectedNewMessageCount = 0
      if channel.name == testCfg.cLogChannelName:
        expectedNewMessageCount = 1
      if len(messages) != expectedNewMessageCount:
        log.Warn("Unexpected message count: {} != {}".format(len(messages), expectedNewMessageCount))
        for message in messages:
          log.Warn("Message: {}: {}".format(message.created_at, message.content))
      self.assertEqual(len(messages), expectedNewMessageCount)
      # TODO Fully verify the release notes message(s)

  def VerifyExpectedUserMessages(self, actualMessages, expectedUsers, expectedMessageFormatsAllUsers, expectedMessageFormatsPerUser):
    dataAllUsers = tu.Container()
    dataAllUsers.amongUsRoleName = testCfg.cAmongUsRoleName
    dataAllUsers.guild = self.guild
    dataAllUsers.botUser = self.loop.run_until_complete(dataAllUsers.guild.fetch_member(self.user.id))
    mappedUsers = []
    expectedMessages = []
    for user in expectedUsers:
      dataPerUser = tu.Container()
      if user == "invalid":
        dataPerUser.user = dataAllUsers.botUser
      else:
        dataPerUser.user = self.loop.run_until_complete(dataAllUsers.guild.fetch_member(user.id))
      mappedUsers.append(dataPerUser.user)
      dataPerUser.amongUsRoleName = dataAllUsers.amongUsRoleName
      dataPerUser.botUser = dataAllUsers.botUser
      dataPerUser.guild = dataAllUsers.guild
      for msg in expectedMessageFormatsPerUser:
        expectedMessages.append(msg.format(data=dataPerUser))
    dataAllUsers.userNamesTicked = "`@{}`".format("`, `@".join(tu.GetNameList(mappedUsers)))
    for msg in expectedMessageFormatsAllUsers:
      expectedMessages.append(msg.format(data=dataAllUsers))
    log.Info("Testing that expected messages were sent: expected={}, actual={}".format(expectedMessages, actualMessages))
    assert len(expectedMessages) == (len(expectedMessageFormatsAllUsers) + (len(expectedMessageFormatsPerUser) * len(expectedUsers)))
    foundMessages = []
    for message in actualMessages:
      found = False
      msgLogDescription = "{} `@{}` @{}: {}".format(message, message.author.name, message.created_at, message.content)
      for expectedMessage in expectedMessages:
        if (message.author.id == dataAllUsers.botUser.id) and (message.content == expectedMessage):
          log.Debug("Found matching message: {}".format(msgLogDescription))
          found = True
          foundMessages.append(message.content)
      if not found:
        log.Debug("Ignoring non-matching message: {}".format(msgLogDescription))
    for expectedMessage in expectedMessages:
      self.assertTrue(expectedMessage in foundMessages)

  def GetGuildBot(self):
    return GuildBotManager.notkBot.guildBots[self.guild.id]

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
      self.client.DeleteChannelByName(channelName)
      self.StartupVerifyShutdown()

  def TestMissingRoles(self):
    for roleName in [ testCfg.cAmongUsRoleName ]:
      log.Info("Testing startup with missing `@{}`".format(roleName))
      self.client.DeleteRoleByName(roleName)
      self.StartupVerifyShutdown()

  def TestPreExistingChannels(self):
    log.Info("Testing startup with existing channels")
    channels = {}
    oldMessages = {}
    tasks = []
    for channel in self.guild.channels:
      if channel.name in testCfg.cChannelNames:
        channels[channel.id] = channel
        tasks.append(self.TestPreExistingChannel(oldMessages, channel))
    self.loop.run_until_complete(asyncio.gather(*tasks))
    log.Info("Verifying that the expected channels were found")
    self.assertEqual(len(testCfg.cChannelNames), len(channels))
    self.assertEqual(len(testCfg.cChannelNames), len(oldMessages))
    log.Info("Starting bot")
    self.StartupVerify()
    log.Info("Verifying that the pre-existing channels still exist")
    self.client.FetchChannels()
    self.assertTrue(all(channelID in self.client.channelsByID for channelID in channels))
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
      for role in self.guild.roles:
        if role.name in testCfg.cRoleNames:
          roles[role.id] = role
          # Ensure that the role has at least one member aside from the bot
          if len(role.members) < 2:
            for member in self.guild.members:
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
      self.client.FetchRoles()
      self.assertTrue(all(roleID in self.client.rolesByID for roleID in roles))
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
