# Modules
import asyncio
import discord
import threading
import time
import unittest as ut
import mysql.connector

from datetime import datetime
from discord.ext import commands
from inspect import currentframe, getframeinfo

# notk-bot
import Error
import Logging as log
import TestExceptions as te
import TestClient

from Config import cfg
from Database import Database
from TestConfig import testCfg

def GetNameDict(ls):
  names = {}
  for entry in ls:
    names[entry.name] = entry
  return names

def GetIDDict(ls):
  ids = {}
  for entry in ls:
    ids[entry.id] = entry
  return ids

async def RunBot():
  # TODO show output based on command-line parameters passed to UT
  # TODO handle errors
  # TODO Possible to run in a thread with its own async loop?
  return await asyncio.create_subprocess_exec("python3", "main.py")
    # stdout=asyncio.subprocess.PIPE,
    # stderr=asyncio.subprocess.PIPE)

class TestData:
  def __init__(self):
    self.cBotChannelName = "notk-bot-test"
    self.cLogChannelName = "notk-bot-test-log"
    self.cAmongUsRoleName = "among-us-test"

    self.cChannelNames = [ self.cBotChannelName, self.cLogChannelName ]
    self.cRoleNames = [ self.cAmongUsRoleName ]

testData = TestData()

class Startup(ut.TestCase):

  def setUp(self):
    self.bot = None
    self.botLaunchTime = None
    # self.loop = asyncio.get_event_loop()
    self.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(self.loop)
    self.client = TestClient.TestClient(discord.Client(), self.loop)
    self.client.database.Connect()
    self.client.database.Clear()
    self.client.Run()
    self.client.WaitUntilReady()
    self.client.ResetGuild()

  def tearDown(self):
    try:
      self.KillBot()
    except:
      # TODO Log a warning if-and-only-if the bot wasn't already killed by the test
      pass

    self.client.database.Clear()
    self.client.ResetGuild()
    self.client.Shutdown()
    self.loop.stop()

  def RunAndWaitForBot(self):
    assert not self.bot
    self.botLaunchTime = datetime.utcnow()
    self.bot = asyncio.run(RunBot())
    self.WaitForBot()

  def WaitForBot(self):
    waited = 0
    while True:
      if waited >= 30:
        Error.Err("Timed out waiting for {}'s bot to come online.".format(self.client.client.guilds[0].name))
      try:
        if self.client.database.GetBotStatus(self.client.client.guilds[0].id) == "RUNNING":
          break
      except Exception as e:
        log.Debug("{}".format(e))
      log.Info("Waiting for bot to come online")
      time.sleep(10)
      waited+= 10

  def ShutdownBot(self):
    if self.bot:
      # TODO Instead of killing the process, signal to the bot that it should shutdown. Also, remove the manual DB manipulation
      self.KillBot()
      self.WaitForBotShutdown()
      self.bot = None

  def KillBot(self):
    if self.bot:
      self.bot.kill()
      time.sleep(2)
      # Since we killed the bot, we need to manually update the status in the DB to prevent us from detecting the bot as
      # 'Running' too early when we next start it.
      if not self.client.database.ShutdownBot(self.client.client.guilds[0].id):
        if self.client.database.GetBotStatus(self.client.client.guilds[0].id) != "OFFLINE":
          Error.Err("Failed to update {}'s bot status (shutdown)".format(self.client.client.guilds[0].name))
      self.bot = None

  def WaitForBotShutdown(self):
    waited = 0
    while self.client.database.GetBotStatus(self.client.client.guilds[0].id) != "OFFLINE":
      if waited > 20:
        Error.Err("Timed out while waiting for {}'s bot to shutdown.".format(self.client.client.guilds[0].name))
      time.sleep(1)
      waited += 1

  def StartupVerify(self):
    self.RunAndWaitForBot()
    self.VerifyStartup()

  def StartupVerifyShutdown(self):
    self.StartupVerify()
    self.ShutdownBot()

  def VerifyClean(self):
    log.Info("Verifying clean state")
    self.assertTrue(all(name not in GetNameDict(self.client.FetchRoles()) for name in testData.cRoleNames))
    self.assertTrue(all(name not in GetNameDict(self.client.FetchChannels()) for name in testData.cChannelNames))

  def VerifyStartup(self):
    log.Info("Verifying existence of all roles")
    self.assertTrue(all(name in GetNameDict(self.client.FetchRoles()) for name in testData.cRoleNames))
    log.Info("Verifying existence of all channels")
    channels = GetNameDict(self.client.FetchChannels())
    self.assertTrue(all(name in channels for name in testData.cChannelNames))
    log.Info("Verifying channels' content.")
    for channelName in channels:
      if channelName == testData.cLogChannelName:
        log.Info("Verifying `#{}` received messages during latest startup.".format(channelName))
        messages = self.client.FetchMessageHistoryAndFlatten(
          channel=channels[channelName],
          limit=1,
          after=self.botLaunchTime)
        self.assertGreater(len(messages), 0)
        # TODO Verify the content of the main channel's messages.
        # TODO Verify pinned messages

  def VerifyStandardRestart(self):
    self.VerifyStartup()
    channels = GetNameDict(self.client.FetchChannels())
    log.Info("Verifying channels' content.")
    for channelName in channels:
      if channelName in testData.cChannelNames:
        log.Info("Verifying `#{}`. ({})".format(channelName, self.botLaunchTime))
        messages = self.client.FetchMessageHistoryAndFlatten(
          channel=channels[channelName],
          limit=1,
          after=self.botLaunchTime)
        expectedNewMessageCount = 0
        if channelName == testData.cLogChannelName:
          expectedNewMessageCount = 1
        if len(messages) != expectedNewMessageCount:
          log.Warn("Unexpected message count: {} != {}".format(len(messages), expectedNewMessageCount))
          for message in messages:
            log.Warn("Message: {}: {}".format(message.created_at, message.content))
        self.assertEqual(len(messages), expectedNewMessageCount)

  def testStartup(self):
    self.TestVirgin()
    self.TestCleanRestart()
    self.TestMissingChannels()
    self.TestMissingRoles()
    self.TestExistingChannels()

  def TestVirgin(self):
    log.Info("Testing virgin startup")
    self.VerifyClean()
    self.StartupVerifyShutdown()

  def TestCleanRestart(self):
    self.RunAndWaitForBot()
    self.VerifyStandardRestart()
    self.ShutdownBot()

  def TestMissingChannels(self):
    for channelName in testData.cChannelNames:
      log.Info("Testing startup with missing `#{}`".format(channelName))
      self.client.DeleteChannel(channelName)
      self.StartupVerifyShutdown()

  def TestMissingRoles(self):
    for roleName in [ testData.cAmongUsRoleName ]:
      log.Info("Testing startup with missing `@{}`".format(roleName))
      self.client.DeleteRole(roleName)
      self.StartupVerifyShutdown()

  def TestExistingChannels(self):
    log.Info("Testing startup with existing channels")
    channels = {}
    oldMessages = {}
    for channel in self.client.client.guilds[0].channels:
      if channel.name in testData.cChannelNames:
        channels[channel.id] = channel
        oldMessages[channel.id] = self.loop.run_until_complete(channel.send(content="test message"))
    log.Info("Verifying that the expected channels were found")
    self.assertEqual(len(testData.cChannelNames), len(channels))
    self.assertEqual(len(testData.cChannelNames), len(oldMessages))
    log.Info("Starting bot")
    self.StartupVerify()
    log.Info("Verifying that the pre-existing channels still exist")
    self.assertTrue(all(channelID in GetIDDict(self.client.FetchChannels()) for channelID in channels))
    log.Info("Verifying that the pre-existing messages still exist")
    for channelID in channels:
      log.Info("Verifying that `#{}`'s messages were preserved".format(channels[channelID].name))
      self.loop.run_until_complete(channels[channelID].fetch_message(oldMessages[channelID].id))
      # FUTURE Verify more messages
      # Reaching here means the message was preserved
    self.ShutdownBot()

  def TestExistingRoles(self):
    log.Info("Testing startup with existing channels")
    roles = {}
    oldMembers = {}
    addedMembers = {}
    try:
      for role in self.client.client.guilds[0].roles:
        if role.name in testData.cRoleNames:
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
      self.assertEqual(len(testData.cRoleNames), len(roles))
      self.assertEqual(len(testData.cRoleNames), len(oldMembers))
      log.Info("Starting bot")
      self.StartupVerify()
      log.Info("Verifying that the pre-existing roles still exist")
      self.assertTrue(all(roleID in GetIDDict(self.client.FetchRoles()) for roleID in roles))
      log.Info("Verifying that the pre-existing role members are still role members")
      log.Info("Testing that all of `@{}`'s members were preserved".format(role.name))
      self.assertTrue(all(member.id in GetIDDict(role.members) for member in oldMembers[role.id] for role in roles))
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

if __name__ == '__main__':
  ut.main()
