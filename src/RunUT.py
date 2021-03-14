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

class NotkTest(ut.TestCase):

  def setUp(self):
    self.bot = None
    self.loop = asyncio.get_event_loop()
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

    # self.client.database.Clear()
    self.client.ResetGuild()
    self.VerifyClean()
    self.client.Shutdown()
    self.loop.stop()

  def VerifyClean(self):
    log.Info("Verifying clean state")
    self.assertTrue(all(name not in CombineNames(self.client.FetchChannels()) for name in testCfg.cChannelNames))
    self.assertTrue(all(name not in CombineNames(self.client.FetchRoles()) for name in testCfg.cRoleNames))

  def VerifySetup(self):
    log.Info("Verifying existence of roles and channels")
    self.assertTrue(all(name in CombineNames(self.client.FetchChannels()) for name in testCfg.cChannelNames))
    self.assertTrue(all(name in CombineNames(self.client.FetchRoles()) for name in testCfg.cRoleNames))

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

  def ShutdownBot(self):
    if self.bot:
      # TODO Instead of killing the process, signal to the bot that it should shutdown. Also, remove the manual DB manipulation
      self.KillBot()
      self.WaitForBotShutdown()
      self.bot = None

  def WaitForBotShutdown(self):
    waited = 0
    while self.client.database.GetBotStatus(self.client.client.guilds[0].id) != "OFFLINE":
      if waited > 20:
        Error.Err("Timed out while waiting for {}'s bot to shutdown.".format(self.client.client.guilds[0].name))
      time.sleep(1)
      waited += 1

  def testSetup(self):
    log.Info("Testing virgin setup")
    self.VerifyClean()
    self.RunAndWaitForBot()
    self.VerifySetup()
    self.ShutdownBot()
    for channelName in [ testCfg.cBotChannelName, testCfg.cLogChannelName ]:
      log.Info("Testing startup with missing `#{}`".format(channelName))
      self.client.DeleteChannel(channelName)
      log.Info("Starting bot")
      self.RunAndWaitForBot()
      self.VerifySetup()
      self.ShutdownBot()

if __name__ == '__main__':
    ut.main()
