# Modules
import asyncio
import time
import unittest as ut

# notk-bot
import Logging as log

import UtilBot

cMaxJoinTimeDefault = 10

async def runBot():
  # TODO show output based on command-line parameters passed to UT
  return await asyncio.create_subprocess_exec("python3", "main.py")
    # stdout=asyncio.subprocess.PIPE,
    # stderr=asyncio.subprocess.PIPE)

async def runUtilBot(*args):
  # TODO show output based on command-line parameters passed to UT
  cmd = "python3 RunUtilBot.py {}".format(" ".join(args))
  testBot = await asyncio.create_subprocess_shell(cmd)
  await testBot.wait()

def resetGuild():
  asyncio.set_event_loop(asyncio.new_event_loop())
  asyncio.run(runUtilBot(UtilBot.cCommandReset))
  time.sleep(3) # TODO figure out why a wait is necessary

class NotkTest(ut.TestCase):

  def setUp(self):
    print("") # newline
    resetGuild()
    asyncio.set_event_loop(asyncio.new_event_loop())
    self.bot = asyncio.run(runBot())
    time.sleep(5)

  def tearDown(self):
    try:
      self.bot.kill()
    except:
      pass
    resetGuild()

  def testStartLog(self):
    myvar = 0
    # TODO Test that the relevant messages, channels, roles, etc. were created in a timed out loop

if __name__ == '__main__':
    ut.main()
