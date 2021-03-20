# Standard
import asyncio

async def AwaitTasks(tasks):
  for task in tasks:
    await task

def WaitForTasks(loop, tasks):
  loop.run_until_complete(AwaitTasks(tasks))
