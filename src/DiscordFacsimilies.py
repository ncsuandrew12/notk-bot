# Modules
# import discord

# notk-bot
from Config import cfg

class AuthorStubbed:
  def __init__(self, guildName):
    self.guildName = guildName
    self.mention = None
    self.name = cfg.cBotName

  async def send(self, msg):
    print("{}| {}.{}: \"sending\" to fake author: {}".format(self.name.upper(), self.guildName, self.name, msg))

class ContextStubbed:
  def __init__(self, guild, author):
    self.author = author
    self.guild = guild
