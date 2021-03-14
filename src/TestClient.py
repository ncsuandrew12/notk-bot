# Modules
import argparse
import discord

from inspect import currentframe, getframeinfo

# notk-bot
import GuildBot
import Logging as log

from Config import cfg
from Database import Database
from TestConfig import testCfg

class TestClient:
  def __init__(self, client, loop):
    self.args = []
    self.client = client
    self.loop = loop
    self.database = Database(self.loop)

  def Run(self):
    log.Info("Starting up")
    self.loop.create_task(self.client.start(cfg.cToken))

  def WaitUntilReady(self):
    self.loop.run_until_complete(self.client.wait_until_ready())
    log.Info("Client is ready")

  def Shutdown(self):
    log.Debug("Shutting down")
    self.loop.run_until_complete(self.client.logout()) #close?

  def FetchChannels(self):
    return self.loop.run_until_complete(self.client.guilds[0].fetch_channels())

  def FetchRoles(self):
    return self.loop.run_until_complete(self.client.guilds[0].fetch_roles())

  def DeleteChannel(self, channelName):
    self.DeleteChannels([channelName])

  def DeleteChannels(self, channelNames):
    self.DeleteByName(self.FetchChannels(), channelNames)

  def DeleteRole(self, roleName):
    self.DeleteRoles([roleName])

  def DeleteRoles(self, roleNames):
    self.DeleteByName(self.FetchRoles(), roleNames)

  def DeleteByName(self, objects, names):
    for obj in objects:
      if obj.name in names:
        log.Info("Deleting {}".format(obj.name))
        self.loop.run_until_complete(obj.delete())

  def ResetGuild(self,):
    log.Info("Resetting guild")
    # Do this instead of looping on DeleteChannel for efficiency
    self.DeleteChannels(testCfg.cChannelNames)
    self.DeleteRoles(testCfg.cRoleNames)
    log.Info("Guild reset")
    # TODO Delete all messages by the client.
