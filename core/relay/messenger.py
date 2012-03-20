'''
Created on Jun 13, 2011

@author: thatcherclay
'''

import smtplib
#from config import settings
from web import settings

class Messenger(object):
  # I am abstract!  Do not use me!
    def __init__(self):
        self.establishConnection()
    
    def send(self, sender_email, recipients, message):
        try:
            self.connection.sendmail(sender_email,recipients,message)
        except:
            self.establishConnection()
            self.connection.sendmail(sender_email,recipients,message)

class SendGridMessenger(Messenger):
    
    def establishConnection(self):
        self.connection = smtplib.SMTP('smtp.sendgrid.net')
        self.connection.login(settings.SENDGRID['username'], settings.SENDGRID['password'])
            
class LocalhostMessenger(object):
    def establishConnection(self):
        self.connection = smtplib.SMTP('localhost')

class AuthenticatedMessenger(Messenger):
  def __init__(self, address, port, username, password):
    self.address = address
    self.port = port
    self.username = username
    self.password = password
    Messenger.__init__(self)
    
  def establishConnection(self):
    self.connection = smtplib.SMTP(self.address, self.port)
    self.connection.login(self.username, self.password)