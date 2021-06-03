# Standard
import asyncio
import argparse

from inspect import currentframe, getframeinfo

# Modules
import discord

# Local
import TestUtil as tu

from Config import cfg
from Database import Database
from LoggingTest import logger as log
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
    log.info("Starting up")
    self.loop.create_task(self.client.start(cfg.cToken))

  def WaitUntilReady(self):
    self.loop.run_until_complete(self.client.wait_until_ready())
    log.info("Client is ready")

  def Shutdown(self):
    log.debug("Shutting down")
    self.loop.run_until_complete(self.client.logout()) #close?

  def FetchStuff(self):
    tasks = []
    tasks.append(self.loop.create_task(self.FetchChannelsAsync()))
    tasks.append(self.loop.create_task(self.FetchMembersAsync()))
    tasks.append(self.loop.create_task(self.FetchRolesAsync()))
    self.loop.run_until_complete(asyncio.gather(*tasks))

  def FetchChannels(self):
    self.loop.run_until_complete(self.FetchChannelsAsync())
    return self.channels

  async def FetchChannelsAsync(self):
    self.channels = await self.client.guilds[0].fetch_channels()
    self.channelsByID = tu.GetIDDict(self.channels)
    self.channelsByName = tu.GetNameDict(self.channels)

  def FetchMembers(self, limit=None, role=None):
    self.loop.run_until_complete(asyncio.gather(self.FetchMembersAsync(limit=limit)))
    if role == None:
      return self.members
    members = []
    for member in self.members:
      if role.id in tu.GetIDDict(member.roles):
        members.append(member)
    return members

  async def FetchMembersAsync(self, limit=None):
    self.members = await self.client.guilds[0].fetch_members(limit=limit).flatten()
    self.membersByID = tu.GetIDDict(self.members)

  def FetchRoles(self):
    self.loop.run_until_complete(self.FetchRolesAsync())
    return self.channels

  async def FetchRolesAsync(self):
    self.roles = await self.client.guilds[0].fetch_roles()
    self.rolesByID = tu.GetIDDict(self.roles)
    self.rolesByName = tu.GetNameDict(self.roles)

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

  def RemoveAllMembersFromRole(self, role, reason = None):
    log.debug("Removing all members from role: %s", role.name)
    self.RemoveMembersFromRole(role, self.FetchMembers(role=role), reason=reason)

  def RemoveMembersFromRole(self, role, members, reason = None):
    tasks = []
    for member in members:
      tasks.append(member.remove_roles(role, reason=reason))
    self.loop.run_until_complete(asyncio.gather(*tasks))

  def RemoveMemberFromRole(self, role, member, reason = None):
    return self.loop.run_until_complete(member.remove_roles(role, reason=reason))

  def CreateChannel(self, name, topic = None, reason = None):
    return self.loop.run_until_complete(
      self.client.guilds[0].create_text_channel(name=name, topic=topic, reason=reason))

  def DeleteChannelByName(self, channelName):
    self.loop.run_until_complete(asyncio.gather(*self.DeleteChannels([channelName])))

  def DeleteChannels(self, channelNames):
    return self.DeleteByKey(self.channelsByName, channelNames)

  def DeleteChannelsByID(self, channelIDs):
    return self.DeleteByKey(self.channelsByID, channelIDs)

  def DeleteRoleByName(self, roleName):
    self.loop.run_until_complete(asyncio.gather(*self.DeleteRoles([roleName])))

  def DeleteRoles(self, roleNames):
    return self.DeleteByKey(self.rolesByName, roleNames)

  def DeleteByKey(self, objects, keys):
    delKeys = []
    for key in objects:
      if key in keys:
        delKeys.append(key)
    tasks = []
    for key in delKeys:
      log.info("Deleting %s (%s)", objects[key].name, key)
      tasks.append(self.loop.create_task(objects[key].delete()))
      del objects[key]
    return tasks

  def ResetGuild(self):
    log.info("Resetting guild")
    # Do this instead of looping on DeleteChannel for efficiency
    self.FetchStuff()
    tasks = self.DeleteChannels(testCfg.cTestChannelNames + testCfg.cChannelNames) + self.DeleteRoles(testCfg.cRoleNames)
    self.loop.run_until_complete(asyncio.gather(*tasks))
    self.FetchStuff()
    if testCfg.cTestChannelName in self.channelsByName:
      self.testChannel = self.channelsByName[testCfg.cTestChannelName]
    log.info("Guild reset")
    # TODO Delete all messages by the client.

  def Setup(self):
    self.FetchChannels()
    if not testCfg.cTestChannelName in self.channelsByName:
      self.testChannel = self.CreateChannel(testCfg.cTestChannelName, "test", "testing")

  def SendToChannel(self, channelID, client=None, content=""):
    if not client:
      client = self.client
    self.FetchChannels()
    channel = client.get_channel(channelID)
    return self.loop.run_until_complete(channel.send(content=content))
