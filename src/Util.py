# Modules
import asyncio
# import discord
# import inspect

# from discord.ext import commands
# from inspect import currentframe, getframeinfo

# notk-bot
# import Error
# import Logging as log

# from Config import cfg
# from GuildBot import GuildBot
# from Exceptions import MinorException
# from Exceptions import NotkException

async def AwaitTasks(tasks):
  for task in tasks:
    await task

def WaitForTasks(loop, tasks):
  loop.run_until_complete(AwaitTasks(tasks))
