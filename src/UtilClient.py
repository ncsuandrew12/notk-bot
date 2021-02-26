# Modules
import argparse
import discord

from inspect import currentframe, getframeinfo

# notk-bot
import GuildBot
import Logging as log

from Config import cfg

cCommandList = "list"
cCommandReset = "reset"

class UtilClient:
  def __init__(self, client, loop):
    global cCommandList
    global cCommandReset
    self.args = []
    self.client = client
    self.cCommandList = cCommandList
    self.cCommandReset = cCommandReset
    self.loop = loop

  def Run(self):
    log.info("Starting up")
    self.loop.create_task(self.client.start(cfg.cToken))

  def WaitUntilReady(self):
    self.loop.run_until_complete(self.client.wait_until_ready())
    log.info("Client is ready")

  def OnReady(self):
    self.guildBot = GuildBot.GuildBot(self.client, self.client.guilds[0], self.loop)
    self.loop.run_until_complete(self.guildBot.startup())

  def Close(self):
    log.debug("Shutting down")
    self.loop.run_until_complete(self.client.logout()) #close?

  def ResetGuild(self, cfg):
    log.info("Resetting guild")
    for channel in self.guildBot.guild.channels:
      if channel.name in cfg.cChannelNames:
        log.info("Deleting #{}".format(channel.name))
        self.loop.run_until_complete(channel.delete())
    for role in self.guildBot.guild.roles:
      if role.name in cfg.cRoleNames:
        log.info("Deleting @{}".format(role.name))
        self.loop.run_until_complete(role.delete())
    log.info("Guild reset")
    # TODO Delete all messages by the client.
