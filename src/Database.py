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

  def Execute(self, sqlStatement):
    # log.debug("Executing SQL statement: {}".format(sqlStatement))
    self.cursor.execute(sqlStatement)
    # log.debug("Previous SQL statement returned {} rows".format(self.cursor.rowcount))
    warnings = self.cursor.fetchwarnings()
    if bool(warnings):
      log.warn("SQL statement returned {} warnings: {}".format(len(warnings), sqlStatement))
      for warning in warnings:
        log.warn("{}".format(warning))

  def Clear(self):
    self.Execute("DROP TABLE IF EXISTS botStatus")

  def Setup(self):
    self.Execute("CREATE TABLE IF NOT EXISTS botStatus (id INT PRIMARY KEY, status VARCHAR(20) NOT NULL)")

  def StartBot(self):
    # TODO bot ID
    self.Execute("SELECT EXISTS(SELECT * FROM botStatus WHERE id = 1 AND status = 'STARTING')")
    if self.cursor.rowcount > 0:
      return
    self.Execute("UPDATE botStatus SET status = 'STARTING' WHERE id=1")
    if self.cursor.rowcount < 1:
      self.Execute("INSERT INTO botStatus VALUES(1, 'STARTING')")
      if self.cursor.rowcount < 1:
        Error.err("Unexpected bot status insert failure")

  def BotStarted(self):
    # TODO bot ID
    self.Execute("SELECT * FROM botStatus WHERE id = 1 AND status != 'RUNNING'")
    if self.cursor.rowcount > 0:
      self.Execute("UPDATE botStatus SET status = 'RUNNING' WHERE id=1")
      if self.cursor.rowcount < 1:
        Error.err("Unexpected bot status update failure")
    else:
      self.Execute("SELECT * FROM botStatus WHERE id = 1 AND status = 'RUNNING'")
      if self.cursor.rowcount < 1:
        self.Execute("INSERT INTO botStatus VALUES(1, 'RUNNING')")
        if self.cursor.rowcount < 1:
          Error.err("Unexpected bot status insert failure")

  def ShutdownBot(self):
    # TODO bot ID
    self.Execute("UPDATE botStatus SET status = 'OFFLINE' WHERE id=1")
    if self.cursor.rowcount < 1:
      Error.err("Unexpected bot status update failure")

  def GetBotStatus(self):
    # TODO bot ID
    def task():
      self.Execute("SELECT status FROM botStatus WHERE id = 1")
      if self.cursor.rowcount == 1:
        return self.cursor.fetchone()[0]
      elif self.cursor.rowcount == 0:
        return "OFFLINE"
      else:
        Error.err("Unexpected SQL result while querying bot status")
    status = task()
    return status


