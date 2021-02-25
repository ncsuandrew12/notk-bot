# Modules
import discord

# notk-bot
import GuildBot
import Logging as log

from Config import cfg

cCommandReset = "reset"

class UtilBot:
  def __init__(self, bot, *args):
    global cCommandReset
    self.args = args
    self.bot = bot
    self.cCommandReset = cCommandReset

  def Run(self):
    self.bot.run(cfg.cToken)
  
  async def OnReady(self):
    self.guildBot = GuildBot.GuildBot(self.bot, self.bot.guilds[0])
    await self.guildBot.startup()

  async def Close(self):
    log.debug("Closing")
    await self.bot.logout() #close?

  async def RunCommand(self):
    log.debug("Processing command: {}".format(" ".join(self.args)))
    cmd = self.args[0]
    if cmd == self.cCommandReset:
      await self.Reset()
    else:
      Error.err(self, ctx, "Invalid command `{}`.".format(cmd))

  async def Reset(self):
    for channel in self.guildBot.botChannels:
      log.info("Deleting #{}".format(channel.name))
      await channel.delete()
    for role in self.guildBot.botRoles:
      log.info("Deleting @{}".format(role.name))
      await role.delete()
    # TODO Delete all messages by the bot.
