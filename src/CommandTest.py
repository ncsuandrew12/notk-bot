# Standard

# Local
import GuildBotManager
import TestUtil as tu
from BotInProcessTest import BotInProcessTest
from BotInProcessTester import BotInProcessTester
from Logging import logger as log
from TestConfig import testCfg

# TODO move
class RoleRoll:
  def __init__(self, enrolled, notEnrolled):
    self.enrolled = enrolled
    # This is *not* a comprehensive list of non-enrolled users. It is an often-empty list of users known to not be
    # enrolled.
    self.notEnrolled = notEnrolled

class CommandTest(BotInProcessTest):

  bt = None

  def setUpClass():
    BotInProcessTester.bt = BotInProcessTester()
    BotInProcessTester.bt.SetUpTester()
    BotInProcessTester.bt.RunAndWaitForBot()

  def tearDownClass():
    BotInProcessTester.bt.TearDownTester()
    BotInProcessTester.bt = None

  def setUp(self):
    if not self.bt:
      self.bt = BotInProcessTester.bt
    self.bt.client.RemoveAllMembersFromRole(self.bt.guildBot.roleAmongUs)

  def tearDown(self):
    self.bt.client.RemoveAllMembersFromRole(self.bt.guildBot.roleAmongUs)

  def RunAmongUsCommandJoin(self, users):
    args = self.PrepAmongUsCommandUserArgs(users)
    self.bt.loop.run_until_complete(self.bt.loop.create_task(
      GuildBotManager.notkBot.Command(self.bt.guildBot.GetDiscordContextStub(), testCfg.cCommandJoin, *args)))

  def RunAmongUsCommandLeave(self, users):
    args = self.PrepAmongUsCommandUserArgs(users)
    self.bt.loop.run_until_complete(self.bt.loop.create_task(
      GuildBotManager.notkBot.Command(self.bt.guildBot.GetDiscordContextStub(), testCfg.cCommandLeave, *args)))

  def RunAmongUsCommandNewGame(self, gameCode):
    args = [ gameCode ]
    self.bt.loop.run_until_complete(self.bt.loop.create_task(
      GuildBotManager.notkBot.Command(self.bt.guildBot.GetDiscordContextStub(), testCfg.cCommandNewGame, *args)))

  def PrepAmongUsCommandUserArgs(self, users):
    args = []
    for user in users:
      if user == "invalid":
        # Member parameters must be tagged. Therefore, a simple name is invalid.
        args.append(self.bt.guildBot.bot.user.name)
      else:
        args.append(user.mention)
    return args

  def VerifyAmongUsRole(self, roleRoll):
    # "Actual" indicates actual users, not that this roll has already been verified.
    actualRoll = self.ConvertRollToActualUsers(roleRoll)
    log.info("Testing that all expected role members are enrolled: %s: %s",
      self.bt.guildBot.roleAmongUs.id,
      actualRoll.enrolled)
    for user in actualRoll.enrolled:
      userRoles = tu.GetIDDict(user.roles)
      log.info("Testing that %s is enrolled in %s:\n%s", user, self.bt.guildBot.roleAmongUs.id, userRoles)
      self.assertTrue(self.bt.guildBot.roleAmongUs.id in userRoles)

  def ConvertRollToActualUsers(self, roleRoll):
    actualRoll = RoleRoll([], [])
    for user in roleRoll.enrolled:
      actualRoll.enrolled.append(self.bt.loop.run_until_complete(self.bt.guildBot.guild.fetch_member(user.id)))
    for user in roleRoll.notEnrolled:
      actualRoll.notEnrolled.append(self.bt.loop.run_until_complete(self.bt.guildBot.guild.fetch_member(user.id)))
    return actualRoll
