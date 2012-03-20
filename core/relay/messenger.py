import smtplib

'''
  A basic messenger for connecting to and sending mail through an outbound
  email provider.  This messenger does not do any authentication.
'''
class Messenger(object):
    def __init__(self, address, port):
      self.address = address
      self.port = port
      self.establishConnection()

    def establishConnection(self):
      self.connection = smtplib.SMTP(self.address, self.port)

    def send(self, sender_email, recipients, message):
        try:
            self.connection.sendmail(sender_email,recipients,message)
        except:
            self.establishConnection()
            self.connection.sendmail(sender_email,recipients,message)

'''
  A messenger for sending mail through a SMTP server running on the default
  port of localhost.  Useful mostly for testing
'''
class LocalhostMessenger(Messenger):
    def __init__(self):
      Messenger.__init__(self, 'localhost', 25)

'''
  An authenticating version of the messenger, using username/password authentication
'''
class AuthenticatedMessenger(Messenger):
  def __init__(self, address, port, username, password):
    self.username = username
    self.password = password
    Messenger.__init__(self, address, port)
    
  def establishConnection(self):
    self.connection = smtplib.SMTP(self.address, self.port)
    self.connection.login(self.username, self.password)