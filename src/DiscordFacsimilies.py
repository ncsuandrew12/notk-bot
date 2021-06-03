class DiscordContextStub:
  def __init__(self, guild, author):
    self.author = author
    self.guild = guild
    # TODO send messages in tests. They can't trigger the commands, but we can at least test the deletion functionality
    self.message = None
