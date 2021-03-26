# Standard

# Local
import GuildBotManager
from BotTester import BotTester

class BotInProcessTester(BotTester):

  def LaunchBot(self):
    GuildBotManager.notkBot.Run()
    return GuildBotManager.notkBot

  def TerminateBot(self):
    self.bot.Shutdown()

  def RunAndWaitForBot(self):
    BotTester.RunAndWaitForBot(self)
    self.guildBot = GuildBotManager.notkBot.guildBots[self.guild.id]
    self.guild = self.guildBot.guild
    self.user = self.loop.run_until_complete(self.guild.fetch_member(self.guildBot.bot.user.id))
