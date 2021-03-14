# Modules
import asyncio
import discord
import threading
import time
import unittest as ut
import mysql.connector

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

def CombineNames(ls):
  names = []
  for entry in ls:
    names.append(entry.name)
  return names

async def RunBot():
  # TODO show output based on command-line parameters passed to UT
  # TODO handle errors
  return await asyncio.create_subprocess_exec("python3", "main.py")
    # stdout=asyncio.subprocess.PIPE,
    # stderr=asyncio.subprocess.PIPE)

class Startup(ut.TestCase):

  def setUp(self):
    self.bot = None
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
    self.VerifySetup()

  def StartupVerifyShutdown(self):
    self.StartupVerify()
    self.ShutdownBot()

  def VerifyClean(self):
    log.Info("Verifying clean state")
    self.assertTrue(all(name not in CombineNames(self.client.FetchChannels()) for name in testCfg.cChannelNames))
    self.assertTrue(all(name not in CombineNames(self.client.FetchRoles()) for name in testCfg.cRoleNames))

  def VerifySetup(self):
    log.Info("Verifying existence of all channels")
    self.assertTrue(all(name in CombineNames(self.client.FetchChannels()) for name in testCfg.cChannelNames))
    log.Info("Verifying existence of all roles")
    self.assertTrue(all(name in CombineNames(self.client.FetchRoles()) for name in testCfg.cRoleNames))

  def testStartup(self):
    self.TestStartupVirgin()
    self.TestStartupMissingChannels()
    self.TestStartupMissingRoles()
    self.TestStartupExistingChannels()

  def TestStartupVirgin(self):
    log.Info("Testing virgin startup")
    self.VerifyClean()
    self.StartupVerifyShutdown()

  def TestStartupMissingChannels(self):
    for channelName in [ testCfg.cBotChannelName, testCfg.cLogChannelName ]:
      log.Info("Testing startup with missing `#{}`".format(channelName))
      self.client.DeleteChannel(channelName)
      self.StartupVerifyShutdown()

  def TestStartupMissingRoles(self):
    for roleName in [ testCfg.cAmongUsRoleName ]:
      log.Info("Testing startup with missing `@{}`".format(roleName))
      self.client.DeleteRole(roleName)
      self.StartupVerifyShutdown()

  def TestStartupExistingChannels(self):
    log.Info("Testing startup with existing channels")
    channelNames = [ testCfg.cBotChannelName, testCfg.cLogChannelName ]
    channels = {}
    oldMessages = {}
    for channel in self.client.client.guilds[0].channels:
      if channel.name in channelNames:
        channels[channel.name] = channel
        oldMessages[channel.name] = self.loop.run_until_complete(channel.send(content="test message"))
    self.assertEqual(len(channelNames), len(channels))
    self.assertEqual(len(channelNames), len(oldMessages))
    self.StartupVerify()
    for channelName in oldMessages:
      log.Info("Testing that `#{}`'s messages were preserved".format(channelName))
      self.loop.run_until_complete(channels[channelName].fetch_message(oldMessages[channelName].id))
      # Reaching here means the message was preserved
    self.ShutdownBot()

if __name__ == '__main__':
  self.startup()
  ut.main()
  self.tearDown()
