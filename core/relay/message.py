from zope.interface import implements
from twisted.mail import smtp
from twisted.internet import defer, threads
from email import message_from_string

'''
  Your basic SMTP Message Delivery service, very vanilla.

  To do any interesting operations, either override this class
  or make use of the flexible ExtensibleSmtpRelayMessageDelivery
  class below
'''
class BaseSmtpRelayMessageDelivery(object):
  implements(smtp.IMessageDelivery)

  def __init__(self, *args, **kwargs):
    self.recipient = None
    self.origin = None
    self.messenger = kwargs["messenger"]
    self.message_processors = kwargs["processors"]

  def receivedHeader(self, helo, origin, recipients):
    self.recipients = recipients

  def validateFrom(self, helo, origin):
    if self.origin == None:
      self.origin = origin
    return origin

  def validateTo(self, user):
    if self.recipient == None:
      self.recipient = user
    return lambda: SmtpRelayMessage(self.recipient, self.origin, self.messenger, self.message_processors)

'''
  An extensible delivery object that supports
  extensible hooks to add your own processing functions.
  Calls to add processing functions can be chained, and will
  be evaluated in LIFO order.
'''
class ExtensibleSmtpRelayMessageDelivery(BaseSmtpRelayMessageDelivery):
  implements(smtp.IMessageDelivery)

  def __init__(self, *args, **kwargs):
    self.recipient = None
    BaseSmtpRelayMessageDelivery.__init__(self, *args, **kwargs)

  def add_validate_from(self, processor):
    original = self.validateFrom
    def wrapper(helo, origin):
			processor(self, helo, origin)
			return original(helo, origin)
    self.validateFrom = wrapper
    return self

  def add_validate_to(self, processor):
    original = self.validateTo
    def wrapper(user):
			user = processor(self, user)
			return original(user)
    self.validateTo = wrapper
    return self


class SmtpRelayMessage(object):
  implements(smtp.IMessage)

  def __init__(self,*args, **kwargs):
    self.lines = []
    self.recipient = kwargs["recipient"]
    self.origin = kwargs["origin"]
    self.messenger = kwargs["messenger"]
    self.message_processors = kwargs["processors"]

  def lineReceived(self, line):
      self.lines.append(line)

  def processMessage(self, message):
    m = message_from_string(message)
    m.replace_header('To', self.redirect)
    for processor in self.message_processors:
      m = processor(m)
    return m

  def sendMessage(self, message):
    self.messenger.send(message['From'], [self.redirect], message.as_string())

  def eomReceived(self):
    message = "\n".join(self.lines)
    d = threads.deferToThread(self.processMessage,message)
    d.addCallback(self.sendMessage)
    return d

  def connectionLost(self):
    # There was an error, throw away the stored lines
    self.lines = None