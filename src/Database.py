# Modules
import mysql.connector

# Local
import Error
# import TestExceptions as te

from Config import cfg
from Logging import logger as log

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

  def Close(self):
    self.cursor = None
    self.connection.close()
    self.connection = None

  def Execute(self, sqlStatement, sqlParams=None):
    # log.debug("Executing SQL statement: %s", sqlStatement)
    sqlIter = self.cursor.execute(sqlStatement, sqlParams)
    # log.debug("Previous SQL statement returned %d rows", self.cursor.rowcount)
    warnings = self.cursor.fetchwarnings()
    if bool(warnings):
      log.warning("SQL statement returned %d warnings: %s%s",
        len(warnings),
        sqlStatement,
        "; params: {}".format(sqlParams) if bool(sqlParams) else "")
      for warning in warnings:
        log.warning("%s", warning)
    return sqlIter

  def Clear(self):
    sqlParams = { "dbName" : cfg.cDbName }
    # Avoids a warning
    self.Execute(
      "SELECT * FROM information_schema.TABLES WHERE TABLE_SCHEMA = %(dbName)s AND TABLE_NAME = 'botStatus'",
      sqlParams)
    if self.cursor.rowcount > 0:
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
          Error.Err("Unexpected bot status insert failure")

  def BotStarted(self, botID):
    sqlParams = { "botID" : botID }
    self.Execute("SELECT * FROM botStatus WHERE id = %(botID)s AND status != 'RUNNING'", sqlParams)
    if self.cursor.rowcount > 0:
      self.Execute("UPDATE botStatus SET status = 'RUNNING' WHERE id=%(botID)s", sqlParams)
      if self.cursor.rowcount < 1:
        Error.Err("Unexpected bot status update failure")
    else:
      self.Execute("SELECT * FROM botStatus WHERE id = %(botID)s AND status = 'RUNNING'", sqlParams)
      if self.cursor.rowcount < 1:
        self.Execute("INSERT INTO botStatus VALUES(%(botID)s, 'RUNNING')", sqlParams)
        if self.cursor.rowcount < 1:
          Error.Err("Unexpected bot status insert failure")

  def ShutdownBot(self, botID):
    sqlParams = { "botID" : botID }
    self.Execute("UPDATE botStatus SET status = 'OFFLINE' WHERE id=%(botID)s", sqlParams)
    self.Execute("SELECT * FROM botStatus WHERE id = %(botID)s AND status = 'OFFLINE'", sqlParams)
    return self.cursor.rowcount > 0

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
        Error.Err("Unexpected SQL result while querying bot status")
    status = task()
    log.debug("Returning status for bot %s: %s", botID, status)
    return status


