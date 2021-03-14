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
import Logging as log
import TestExceptions as te
import TestClient

from Config import cfg
from Database import Database
from TestConfig import testCfg

def combineNames(ls):
  names = []
  for entry in ls:
    names.append(entry.name)
  return names

async def runBot():
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
    self.verifyClean()
    self.client.Shutdown()
    self.loop.stop()

  def testSetup(self):
    self.verifyClean()
    self.RunAndWaitForBot()
    self.verifySetup()
    self.KillBot()
    for channelName in [ testCfg.cBotChannelName, testCfg.cLogChannelName ]:
      self.client.DeleteChannel(channelName)
      self.RunAndWaitForBot()
      self.KillBot()

  def RunAndWaitForBot(self):
    assert not self.bot
    self.bot = asyncio.run(runBot())
    self.WaitForBot()

  def KillBot(self):
    # TODO Instead of killing the process, signal to the bot that it should shutdown
    self.bot.kill()
    time.sleep(2)
    # Since we killed the bot, we need to manually update the status in the DB to prevent us from detecting the bot as
    # 'Running' too early when we next start it.
    if not self.client.database.ShutdownBot(self.client.client.guilds[0].id):
      Error.err("Failed to update {}'s bot status (shutdown)".format(self.client.client.guilds[0].name))
    self.bot = None

  def verifyClean(self):
    log.info("Verifying clean state")
    self.assertTrue(all(name not in combineNames(self.client.FetchChannels()) for name in testCfg.cChannelNames))
    self.assertTrue(all(name not in combineNames(self.client.FetchRoles()) for name in testCfg.cRoleNames))

  def verifySetup(self):
    log.info("Verifying existence of roles and channels")
    self.assertTrue(all(name in combineNames(self.client.FetchChannels()) for name in testCfg.cChannelNames))
    self.assertTrue(all(name in combineNames(self.client.FetchRoles()) for name in testCfg.cRoleNames))

  def WaitForBot(self):
    while True:
      try:
        if self.client.database.GetBotStatus(self.client.client.guilds[0].id) == "RUNNING":
          break
      except Exception as e:
        log.debug("{}".format(e))
      log.info("Wating for bot to come online")
      time.sleep(10)

  # def WaitForBotShutdown():
  #   waited = 0
  #   while self.database.GetBotStatus(self.client.client.guilds[0].id) != "OFFLINE":
  #     if waited > 20:
  #       Error.err("Timed out while waiting for {}'s bot to shutdown.".format(self.client.client.guilds[0].name))
  #     time.sleep(1)
  #     waited += 1

if __name__ == '__main__':
    ut.main()
