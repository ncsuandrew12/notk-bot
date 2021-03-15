# Modules
import asyncio

# notk-bot

def GetNameDict(ls, filterNames = None):
  names = {}
  for entry in ls:
    if (not filterNames) or (entry.name in filterNames):
      names[entry.name] = entry
  return names

def GetIDDict(ls):
  ids = {}
  for entry in ls:
    ids[entry.id] = entry
  return ids

async def RunBot():
  # TODO show output based on command-line parameters passed to UT
  # TODO handle errors
  # TODO Possible to run in a thread with its own async loop?
  return await asyncio.create_subprocess_exec("python3", "main.py")
    # stdout=asyncio.subprocess.PIPE,
    # stderr=asyncio.subprocess.PIPE)

class Container:
  pass
