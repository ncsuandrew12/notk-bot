# Standard
import argparse

from inspect import currentframe, getframeinfo

# Modules
import discord

# Local
import Logging as log
import TestUtil as tu

from Config import cfg
from Database import Database
from TestConfig import testCfg

class TestClient:
  def __init__(self, loop):
    self.args = []
    intents = discord.Intents.default()
    intents.members = True
    self.client = discord.Client(intents=intents)
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

  def FetchMembersAndFlatten(self, limit=1000):
    return self.loop.run_until_complete(self.FetchMembersAndFlattenAsync(limit=limit))

  async def FetchMembersAndFlattenAsync(self, limit=1000):
    return await self.client.guilds[0].fetch_members(limit=limit).flatten()

  def FetchRoles(self):
    return self.loop.run_until_complete(self.client.guilds[0].fetch_roles())

  def FetchMessageHistoryAndFlatten(self, channel, limit=100, before=None, after=None, oldestFirst=None):
    return self.loop.run_until_complete(
      self.FetchMessageHistoryAndFlattenAsync(
        channel=channel,
        limit=limit,
        before=before,
        after=after,
        oldestFirst=oldestFirst
      ))

  async def FetchMessageHistoryAndFlattenAsync(self, channel, limit=100, before=None, after=None, oldestFirst=None):
    return await channel.history(
      limit=limit,
      before=before,
      after=after,
      oldest_first=oldestFirst).flatten()

  def RemoveMemberRole(self, member, role, reason = None):
    return self.loop.run_until_complete(member.remove_roles(role, reason=reason))

  def CreateChannel(self, name, topic = None, reason = None):
    return self.loop.run_until_complete(
      self.client.guilds[0].create_text_channel(name=name, topic=topic, reason=reason))

  def DeleteChannel(self, channelName):
    self.DeleteChannels([channelName])

  def DeleteChannels(self, channelNames):
    self.DeleteByName(self.FetchChannels(), channelNames)

  def DeleteChannelsByID(self, channelIDs):
    self.DeleteByID(self.FetchChannels(), channelIDs)

  def DeleteRole(self, roleName):
    self.DeleteRoles([roleName])

  def DeleteRoles(self, roleNames):
    self.DeleteByName(self.FetchRoles(), roleNames)

  def DeleteByID(self, objects, ids):
    for obj in objects:
      if obj.id in ids:
        log.Info("Deleting {} ({})".format(obj.name, obj.id))
        self.loop.run_until_complete(obj.delete())

  def DeleteByName(self, objects, names):
    for obj in objects:
      if obj.name in names:
        log.Info("Deleting {}".format(obj.name))
        self.loop.run_until_complete(obj.delete())

  def ResetGuild(self,):
    log.Info("Resetting guild")
    # Do this instead of looping on DeleteChannel for efficiency
    self.DeleteChannels(testCfg.cTestChannelNames)
    self.DeleteChannels(testCfg.cChannelNames)
    self.DeleteRoles(testCfg.cRoleNames)
    channels = tu.GetNameDict(self.FetchChannels())
    if testCfg.cTestChannelName in channels:
      self.testChannel = channels[testCfg.cTestChannelName]
    else:
      self.testChannel = self.CreateChannel(testCfg.cTestChannelName, "test", "testing")
    log.Info("Guild reset")
    # TODO Delete all messages by the client.

  def SendToChannel(self, channelID, client=None, content=""):
    if not client:
      client = self.client
    self.FetchChannels()
    channel = client.get_channel(channelID)
    return self.loop.run_until_complete(channel.send(content=content))
