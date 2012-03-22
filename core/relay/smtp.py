from zope.interface import implements
import sys,os
import logging

from twisted.internet import defer, threads
from twisted.mail import smtp
from twisted.python import failure, log
from twisted.mail.imap4 import LOGINCredentials, PLAINCredentials
from twisted.cred import credentials, checkers, error as credError
from twisted.cred.portal import IRealm
from twisted.cred.portal import Portal
from twisted.internet import ssl

from core.relay.message import ExtensibleSmtpRelayMessageDelivery


logger = logging.getLogger("smtprelay")
        
class SecureSMTPRelayFactory(smtp.SMTPFactory):
    protocol = smtp.ESMTP
    
    def __init__(self, portal, ctx):
        smtp.SMTPFactory.__init__(self, portal)
        self.ctx = ctx

    def buildProtocol(self, addr):
        p = smtp.SMTPFactory.buildProtocol(self, addr)
        if self.ctx:
          p.ctx = self.ctx
        p.challengers = {"LOGIN": LOGINCredentials, "PLAIN": PLAINCredentials}
        return p

class SMTPRelayRealm:
    implements(IRealm)

    def __init__(self, *args, **kwargs):
        self.messenger = kwargs["messenger"]
        self.processors = [] if "processors" not in kwargs else kwargs["processors"]
        self.audience_config = {"to":[], "from":[]} if "audience_filters" not in kwargs else kwargs["audience_filters"]

    def requestAvatar(self, user, mind, *interfaces):
        if smtp.IMessageDelivery in interfaces:
          message_delivery = ExtensibleSmtpRelayMessageDelivery(user, self.messenger, self.processors)
          for filter in self.audience_config["to"]:
            message_delivery.add_validate_to(filter)
          for filter in self.audience_config["to"]:
            message_delivery.add_validate_from(filter)

          return smtp.IMessageDelivery, message_delivery, lambda: None
        raise Exception("Expecting IMessageDelivery in interfaces")