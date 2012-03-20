from twisted.cred.portal import IRealm
from twisted.mail import smtp
from zope.interface.declarations import implements
from core.relay.message import RedirectMessageDelivery

class RedirectRealm:
    implements(IRealm)

    def __init__(self, *args, **kwargs):
        self.messenger = kwargs["messenger"]

    def requestAvatar(self, user, mind, *interfaces):
        if smtp.IMessageDelivery in interfaces:
            return smtp.IMessageDelivery, RedirectMessageDelivery(self.messenger), lambda: None
        raise NotImplementedError()