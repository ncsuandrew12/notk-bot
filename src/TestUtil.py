# Standard
import asyncio

def GetNameDict(ls, filterNames = None):
  names = {}
  for entry in ls:
    if (not filterNames) or (entry.name in filterNames):
      names[entry.name] = entry
  return names

def GetNameList(ls, filterNames = None):
  names = []
  for entry in ls:
    if (not filterNames) or (entry.name in filterNames):
      names.append(entry.name)
  return names

def GetIDDict(ls):
  ids = {}
  for entry in ls:
    ids[entry.id] = entry
  return ids

class Container:
  pass

class RoleRoll:
  def __init__(self, enrolled, notEnrolled):
    self.enrolled = enrolled
    # This is *not* a comprehensive list of non-enrolled users. It is an often-empty list of users known/expected to not
    # be enrolled.
    self.notEnrolled = notEnrolled
