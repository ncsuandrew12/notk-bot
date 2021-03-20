# Standard
import asyncio

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

class Container:
  pass
