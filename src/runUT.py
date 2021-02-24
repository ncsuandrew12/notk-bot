# Modules
import asyncio
import time
import unittest as ut

# notk-bot
import Logging as log

cMaxJoinTimeDefault = 10

async def runBot():
  # TODO suppress output based on command-line parameters passed to UT
  return await asyncio.create_subprocess_exec("python3", "main.py")
      # stdout=asyncio.subprocess.PIPE,
      # stderr=asyncio.subprocess.PIPE

class NotkTest(ut.TestCase):

  def testStartLog(self):
    # TODO Connect to Discord and delete channels, roles

    self.bot = asyncio.run(runBot())

    time.sleep(3)
    # TODO Test that the relevant messages, channels, roles, etc. were created in a timed out loop

    # TODO move to common location
    self.bot.kill()

    # TODO Clean up after ourselves

if __name__ == '__main__':
    ut.main()
