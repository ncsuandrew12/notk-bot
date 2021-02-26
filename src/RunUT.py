# Modules
import asyncio
import discord
import threading
import time
import unittest as ut

from discord.ext import commands
from inspect import currentframe, getframeinfo

# notk-bot
import Logging as log
import TestExceptions as te
import UtilClient

from Config import cfg
from GuildBotManager import bot

class TestConfig:
  def __init__(self):
    self.cAmongUsRoleName = "among-us{}".format(cfg.cUniversalSuffix)
    self.cBotChannelName = "notk-bot{}".format(cfg.cUniversalSuffix)
    self.cLogChannelName = "notk-bot{}-log".format(cfg.cUniversalSuffix)
    self.cChannelNames = [ self.cBotChannelName, self.cLogChannelName ]
    self.cRoleNames = [ self.cAmongUsRoleName ]

kCfg = TestConfig()

def combineNames(ls):
  names = []
  for entry in ls:
    names.append(entry.name)
  return names

def verifyClean(test):
  log.info("Verifying clean state")
  test.assertTrue(all(name not in combineNames(test.client.client.guilds[0].channels) for name in kCfg.cChannelNames))
  test.assertTrue(all(name not in combineNames(test.client.client.guilds[0].roles) for name in kCfg.cRoleNames))

def verifySetup(test):
  log.info("Verifying existence of roles and channels")
  test.assertTrue(all(name in combineNames(test.client.client.guilds[0].channels) for name in kCfg.cChannelNames))
  test.assertTrue(all(name in combineNames(test.client.client.guilds[0].roles) for name in kCfg.cRoleNames))

def RunSetup(bot):
  bot.SetupGuilds()

class NotkTest(ut.TestCase):

  def setUp(self):
    self.loop = asyncio.get_event_loop()
    self.client = UtilClient.UtilClient(discord.Client(), self.loop)
    self.client.Run()
    self.client.WaitUntilReady()
    self.client.OnReady()
    self.client.ResetGuild(kCfg)
    self.bot = bot
    self.bot.Run()
    self.bot.WaitUntilReady()
    self.bot.OnReady()
    self.bot.StartGuildBots()

  def tearDown(self):
    self.bot.Close()
    self.client.ResetGuild(kCfg)
    verifyClean(self)
    self.client.Close()
    self.loop.stop()

  def testSetup(self):
    verifyClean(self)
    RunSetup(self.bot)
    verifySetup(self)

if __name__ == '__main__':
    ut.main()
