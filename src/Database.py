# Modules
import mysql.connector

# notk-bot
import Error
import Logging as log
# import TestExceptions as te

from Config import cfg

class Database:
  def __init__(self, loop):
    self.loop = loop

  def Connect(self):
    self.connection = mysql.connector.connect(
      host=cfg.cDbHost,
      port=cfg.cDbPort,
      user=cfg.cDbUser,
      password=cfg.cDbPassword,
      database=cfg.cDbName
    )
    self.connection.autocommit = True
    self.connection.get_warnings = True
    self.cursor = self.connection.cursor(buffered=True)

  def Execute(self, sqlStatement, sqlParams=None):
    # log.debug("Executing SQL statement: {}".format(sqlStatement))
    sqlIter = self.cursor.execute(sqlStatement, sqlParams)
    # log.debug("Previous SQL statement returned {} rows".format(self.cursor.rowcount))
    warnings = self.cursor.fetchwarnings()
    if bool(warnings):
      log.warn("SQL statement returned {} warnings: {}{}".format(
        len(warnings),
        sqlStatement,
        "; params: {}".format(sqlParams) if bool(sqlParams) else ""))
      for warning in warnings:
        log.warn("{}".format(warning))
    return sqlIter

  def Clear(self):
    self.Execute("DROP TABLE IF EXISTS botStatus")

  def Setup(self):
    self.Execute("CREATE TABLE IF NOT EXISTS botStatus (id BIGINT PRIMARY KEY, status VARCHAR(20) NOT NULL)")

  def StartBot(self, botID):
    sqlParams = { "botID" : botID }
    self.Execute("SELECT * FROM botStatus WHERE id = %(botID)s AND status = 'STARTING'", sqlParams)
    if self.cursor.rowcount < 1:
      self.Execute("UPDATE botStatus SET status = 'STARTING' WHERE id=%(botID)s", sqlParams)
      if self.cursor.rowcount < 1:
        self.Execute("INSERT INTO botStatus VALUES(%(botID)s, 'STARTING')", sqlParams)
        if self.cursor.rowcount < 1:
          Error.err("Unexpected bot status insert failure")

  def BotStarted(self, botID):
    sqlParams = { "botID" : botID }
    self.Execute("SELECT * FROM botStatus WHERE id = %(botID)s AND status != 'RUNNING'", sqlParams)
    if self.cursor.rowcount > 0:
      self.Execute("UPDATE botStatus SET status = 'RUNNING' WHERE id=%(botID)s", sqlParams)
      if self.cursor.rowcount < 1:
        Error.err("Unexpected bot status update failure")
    else:
      self.Execute("SELECT * FROM botStatus WHERE id = %(botID)s AND status = 'RUNNING'", sqlParams)
      if self.cursor.rowcount < 1:
        self.Execute("INSERT INTO botStatus VALUES(%(botID)s, 'RUNNING')", sqlParams)
        if self.cursor.rowcount < 1:
          Error.err("Unexpected bot status insert failure")

  def ShutdownBot(self, botID):
    sqlParams = { "botID" : botID }
    self.Execute("UPDATE botStatus SET status = 'OFFLINE' WHERE id=1")
    return self.cursor.rowcount < 1

  def GetBotStatus(self, botID):
    # TODO Make bot status enum
    sqlParams = { "botID" : botID }
    def task():
      self.Execute("SELECT status FROM botStatus WHERE id = %(botID)s", sqlParams)
      if self.cursor.rowcount == 1:
        return self.cursor.fetchone()[0]
      elif self.cursor.rowcount == 0:
        return "OFFLINE"
      else:
        Error.err("Unexpected SQL result while querying bot status")
    status = task()
    return status


