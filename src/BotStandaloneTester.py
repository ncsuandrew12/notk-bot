# Standard
import asyncio
import time

# Local
import Error
from BotTester import BotTester

class BotStandaloneTester(BotTester):

  def LaunchBot(self):
    # TODO show output based on command-line parameters passed to UT
    # TODO handle errors
    # TODO Possible to run in a thread with its own async loop?
    return asyncio.run(asyncio.create_subprocess_exec("python3", "main.py"))
      # stdout=asyncio.subprocess.PIPE,
      # stderr=asyncio.subprocess.PIPE)

  def TerminateBot(self):
    self.bot.kill()
    time.sleep(2)
    # Since we killed the bot, we need to manually update the status in the DB to prevent us from detecting the bot as
    # 'Running' too early when we next start it.
    if not self.client.database.ShutdownBot(self.guild.id):
      if self.client.database.GetBotStatus(self.guild.id) != "OFFLINE":
        Error.Err("Failed to update {}'s bot status (shutdown)".format(self.client.client.guilds[0].name))

  def RunAndWaitForBot(self):
    BotTester.RunAndWaitForBot(self)
    self.guild = self.client.client.guilds[0]
    self.user = self.loop.run_until_complete(self.guild.fetch_member(self.client.client.user.id))
