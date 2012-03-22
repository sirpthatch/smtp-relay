from twisted import internet
from twisted.application import service
from twisted.cred import checkers
from twisted.cred.portal import Portal
from twisted.internet import ssl
from twisted.mail.smtp import SMTPFactory
from core.relay.messenger import AuthenticatedMessenger, Messenger, LocalhostMessenger
from core.relay.smtp import SMTPRelayRealm, SMTPRelayFactory, SecureSMTPRelayFactory

class BasicConfiguration(object):

  def __init__(self, config={}):
    self.config = config

  def messenger(self):
    if "OUTBOUND_EMAIL_HOST_USER" in self.config and "OUTBOUND_EMAIL_HOST_PASSWORD" in self.config:
      return AuthenticatedMessenger(self.config["OUTBOUND_EMAIL_HOST"],
                                    self.config["OUTBOUND_EMAIL_PORT"],
                                    self.config["OUTBOUND_EMAIL_HOST_USER"],
                                    self.config["OUTBOUND_EMAIL_HOST_PASSWORD"])
    elif "OUTBOUND_EMAIL_HOST" in self.config:
      return Messenger(self.config["OUTBOUND_EMAIL_HOST"], 25 if "OUTBOUND_EMAIL_PORT" not in self.config else self.config["OUTBOUND_EMAIL_PORT"])
    else:
      return LocalhostMessenger()


  def processors(self):
    return [] if "PROCESSORS" not in self.config else self.config["PROCESSORS"]

  def audience_filters(self):
    return {"to":[], "from":[]} if "AUDIENCE_FILTERS" not in self.config else self.config["AUDIENCE_FILTERS"]

  def auth_checkers(self):
    return [] if "AUTH_CHECKERS" not in self.config else self.config["AUTH_CHECKERS"]

  def realm(self):
    return SMTPRelayRealm(messenger = self.messenger(),
                                   processors=self.processors(),
                                   audience_filters=self.audience_filters())

  def portal(self):
    portal = Portal(self.realm())
    for checker in self.auth_checkers():
      portal.registerChecker(checker)
    if len(self.auth_checkers()) == 0:
      portal.registerChecker(checkers.AllowAnonymousAccess())
    return portal

  def request_factory(self):
    if "KEYS" in self.config:
      security = self.config["KEYS"]
      secureContextFactory = ssl.DefaultOpenSSLContextFactory(
            security["PRIVATE"],
            security["PUBLIC"]
            )
      return SecureSMTPRelayFactory(self.portal(),secureContextFactory)
    else:
      return SMTPFactory(self.portal())

  def application(self):
    factory = self.request_factory()
    a = service.Application(self.config["name"] if "name" in self.config else "SMTP Relay Server")
    ports = [25] if "ports" not in self.config else self.config["ports"]
    for port in ports:
      internet.TCPServer(port, factory).setServiceParent(a)
    return a

