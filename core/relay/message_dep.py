'''
Created on Jun 13, 2011

@author: thatcherclay
'''

from zope.interface import implements
from twisted.mail import smtp
from twisted.internet import defer, threads

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.message import MIMEMessage
from email.message import Message
from email import message_from_string

import re
import uuid
import smtplib
from core.messenger import SendGridMessenger
from web.mailreceipts.models import EmailRecord, EmailEndPoint, CUSTOMER_LEVEL_FREE
from web.mailreceipts.lib.mailer import Mailer
from web import settings as django_settings

from common.config import settings

import logging




logger = logging.getLogger("sugar.message")

regex_from = re.compile('^From: (.*)$', re.M)
regex_to = re.compile('^To: (.*)$', re.M)
regex_subject = re.compile('^Subject: (.*)$', re.M)
regex_bodyend = re.compile('\</body\>', re.M)
regex_display_name = re.compile('(.+)<.*@.*>')

class RedirectMessageDelivery(object):
  implements(smtp.IMessageDelivery)
  
  def __init__(self, messenger):
    self.messenger = messenger
  
  def receivedHeader(self, helo, origin, recipients):
    self.recipients = recipients
  
  def validateFrom(self, helo, origin):
    return origin
  
  def validateTo(self, user):
    # Only messages to @tracker.mailreceipts.com are accepted
    unprocessed_email_address, domain = str(user).split("@")
    if not domain.lower() == "tracker.mailreceipts.com":
      logger.warn('Attempt to send to a bad domain: %s'%domain)
      raise smtp.SMTPBadRcpt(user)
    username, realdomain = unprocessed_email_address.split('-')

    # Handle yahoo as the exception, they do not allow "yahoo" to appear in the username for an email address
    if realdomain.lower() == 'yaho.com':
      realdomain = 'yahoo.com'

    redirect_email = "%s@%s"%(username, realdomain)
    logger.info("Sending redirected message to %s"%redirect_email)
    return lambda: RedirectMessage(redirect_email, self.messenger)

class RedirectMessage(object):
  implements(smtp.IMessage)
  
  def __init__(self, redirect, messenger):
    self.lines = []
    self.redirect = redirect
    self.messenger = messenger

  def lineReceived(self, line):
      self.lines.append(line)
  
  def processMessage(self, message):
    m = message_from_string(message)
    headersToDelete = []
    for header in m.keys():
      lowerH = header.lower()
      if not lowerH == 'to' and not lowerH == 'from' and not lowerH == 'subject' and not lowerH == 'content-type':
        headersToDelete.append(header)
    for header in headersToDelete:
      del m[header]
    m.replace_header('To', self.redirect)
    m.replace_header('From','confirm@tracker.mailreceipts.com')
    return m
  
  def sendMessage(self, message):
    #print("Message: %s"%(message.as_string()))
    self.messenger.send(message['From'], [self.redirect], message.as_string())
  
  def eomReceived(self):
    message = "\n".join(self.lines)
    d = threads.deferToThread(self.processMessage,message)
    d.addCallback(self.sendMessage)
    return d
  
  def connectionLost(self):
    # There was an error, throw away the stored lines
    self.lines = None

class SugarMessageDelivery(object):
  implements(smtp.IMessageDelivery)
  
  def __init__(self, user, messenger):
    self.authUser = user
    self.sent = False
    self.messenger = messenger
    self.record = EmailRecord()
    self.record.sender = self.authUser
    #self.record.save()
    
  
  def receivedHeader(self, helo, origin, recipients):
    self.recipients = recipients
  
  def validateFrom(self, helo, origin):
    # All addresses are accepted
    return origin

  def validateTo(self, user):
    return lambda: SugarMessage(self.authUser, user, self.messenger, self.record)

    
class SugarMessage(object):
  implements(smtp.IMessage)
  
  def __init__(self, authUser, recipient, messenger, record):
    self.lines = []
    self.authUser = authUser
    self.recipient = recipient
    self.messenger = messenger
    self.record = record
    self.record.save()
    logger.info("In SugarMessage, record id is %d" % self.record.id)

  def lineReceived(self, line):
      self.lines.append(line)

  def processMessage(self, message):
    # Initialize the record if there is one
    if self.record.subject is None:
      recipients = regex_to.search(message).group(1)
      subject = regex_subject.search(message).group(1)
      self.record.subject = subject
      self.record.allRecipients = recipients
      # Something weird is going on here, but this works
      self.record.save(force_update=True)

    # Create the email end point
    endpoint = EmailEndPoint()
    endpoint.email = self.record
    endpoint.recipient = str(self.recipient)
    endpoint.category = str(uuid.uuid4())
    if self.record.sender.get_profile().flag_all_for_alert:
      endpoint.flagged_for_alert = True
    endpoint.save()
    
    m = message_from_string(message)
    
    processed_message = SugarMessageProcessor(self.authUser).process(m, endpoint.category)
    
    self.lines = None
    
    return processed_message
  
  def sendMessage(self, message):
    self.messenger.send(self.authUser.email, [self.recipient], message.as_string())
  
  def eomReceived(self):
    message = "\n".join(self.lines)
    d = threads.deferToThread(self.processMessage,message)
    d.addCallback(self.sendMessage)
    return d
  
  def connectionLost(self):
    # There was an error, throw away the stored lines
    self.lines = None
    
class SugarMessageProcessor(object):
  
  def __init__(self, user):
    self.user = user
  
  def process(self, mime_message, newCategory):
    display_name_match = regex_display_name.search(mime_message["From"])
    if display_name_match:
      mime_message.replace_header('From', "%s<%s>"%(display_name_match.group(1), self.user.email))
    else:
      mime_message.replace_header('From', self.user.email)
    
    if mime_message.is_multipart() and (mime_message.get_content_type() == 'multipart/alternative' or mime_message.get_content_type() == 'multipart/mixed') :
      messages = mime_message.get_payload()
      last_html = None
      last_text = None
      for mess in messages:
        if mess.get_content_type() == 'text/html':
          last_html = mess
        elif mess.get_content_type() == 'text/plain':
          last_text = mess
      if last_html != None or last_text != None:
        if last_html == None:
          html_message = MIMEText(self.wrapHTML(last_text.get_payload(), newCategory), 'html')
          mime_message.attach(html_message)
        else:
          self.injectIntoHTML(last_html, newCategory)
      else:
        logger.error('Unable to inject tracker, message types are %s'%",".join([mess.get_content_type() for mess in messages]))
    elif mime_message.get_content_type() == 'text/plain':
      msg = MIMEMultipart('alternative')
      [msg.add_header(key, mime_message[key]) for key in mime_message.keys()]
      textPart = MIMEText(mime_message.get_payload(), 'plain')
      htmlPart = MIMEText(self.wrapHTML(mime_message.get_payload(), newCategory), 'html')
      msg.attach(textPart)
      msg.attach(htmlPart)
      mime_message = msg
    elif mime_message.get_content_type() == 'text/html':
      self.injectIntoHTML(mime_message, newCategory)
    else:
      logger.error('Unable to inject tracker, message type is %s'%mime_message.get_content_type())
    return mime_message
  
  def getEmailTrackerLink(self, category):
    return "<img src=\"%s/email/%s\" height=\"0\" width=\"0\" style=\"display:None\"></img>"%(settings.SPICE_TRACKER_URL, category)
  
  def getAdvertisingFooter(self):
    if (self.user.get_profile().customer_level != CUSTOMER_LEVEL_FREE):
      return ""
    return "<div style=\"margin-top:40px;width:100%;height:123px\;vertical-align:middle;\"><a href=\"www.mailreceipts.com\"><img alt=\"Mail Receipts\" src=\"http://www.mailreceipts.com/static/images/light-blue/logo-small.png\"></img></a><br/>For more information click <a href=\"www.mailreceipts.com\">here</a>.</div>"
  
  def wrapHTML(self, message_text, category):
    return "<html><body>%s%s%s</body></html>"%(message_text, 
                                               self.getEmailTrackerLink(category), 
                                               self.getAdvertisingFooter())
  
  def injectIntoHTML(self, message, category):
    originalhtml = message.get_payload()
    newhtml = None
    
    if regex_bodyend.search(originalhtml):
        newhtml = regex_bodyend.sub("%s %s</body>"%(self.getEmailTrackerLink(category), self.getAdvertisingFooter()), originalhtml)
    else:
        newhtml = originalhtml+self.getEmailTrackerLink(category) + self.getAdvertisingFooter()
    message.set_payload(newhtml)
  