'''
Created on Jun 13, 2011

@author: thatcherclay
'''
from twisted.trial import unittest
from twisted.mail import smtp
from test.seed import createUser

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from server.message import SugarMessage, SugarMessageProcessor, RedirectMessageDelivery, RedirectMessage
from mailreceipts.models import EmailRecord, CUSTOMER_LEVEL_FREE

import re

import logging, logging.config
logging.config.fileConfig('test/logging.conf')


class RecordingMessenger(object):
    def send(self, sender_email, recipients, message):
        self.sender_email = sender_email
        self.recipients = recipients
        self.message = message

class SugarMessageTestSuite(unittest.TestCase):
    
    def setUp(self):
        self.authUser = createUser("testemail@testcase.com","pass1")
        self.messenger = RecordingMessenger()
        for record in EmailRecord.objects.all():
            record.delete()
        
    def sendmail(self, message,**kwargs):
        if "to" in kwargs:
            message.lineReceived("To: %s"%kwargs["to"])
        else:
            message.lineReceived("To: %s"%("default@testcase.com"))
            
        if "sender" in kwargs:
            message.lineReceived("From: %s"%kwargs["sender"])
        else:
            message.lineReceived("From: %s"%("default@testcase.com"))
            
        if "subject" in kwargs:
            message.lineReceived("Subject: %s"%kwargs["subject"])
        else:
            message.lineReceived("Subject: %s"%("default subject"))
        
        if "text" in kwargs:
            message.lineReceived(kwargs["text"])
        else:
            message.lineReceived("Default Text")
        
        
    
    def test_headerRecipientsParsed(self):
        er = EmailRecord()
        er.sender = self.authUser
        er.save()
        message = SugarMessage(self.authUser, 'recipient@testcase.com',self.messenger, er)
        self.sendmail(message, to="recipient@testcase.com")
        deferred = message.eomReceived()
        deferred.addCallback(lambda check: self.assertEquals("recipient@testcase.com",er.allRecipients))    
    
    def test_headerRecipientListParsed(self):
        er = EmailRecord()
        er.sender = self.authUser
        er.save()
        message = SugarMessage(self.authUser, 'recipient1@testcase.com,recipient2@testcase.com',self.messenger, er)
        self.sendmail(message, to='recipient1@testcase.com,recipient2@testcase.com')
        deferred = message.eomReceived()
        deferred.addCallback(lambda check: self.assertEquals('recipient1@testcase.com,recipient2@testcase.com',er.allRecipients))    
    
    def test_headerSubjectParsed(self):
        er = EmailRecord() 
        er.sender = self.authUser
        er.save() 
        message = SugarMessage(self.authUser, 'recipient@testcase.com',self.messenger, er)
        self.sendmail(message, subject="Parse Me")
        defferred = message.eomReceived()
        defferred.addCallback(lambda check: self.assertEquals("Parse Me", er.subject))
    
    def test_senderReplaced(self):
        er = EmailRecord() 
        er.sender = self.authUser 
        er.save()
        message = SugarMessage(self.authUser, 'recipient@testcase.com',self.messenger, er)
        self.sendmail(message, sender="ghost_email@testcase.com")
        deffered = message.eomReceived()
        deffered.addCallback(lambda check: self.assertEquals(self.authUser.email,self.messenger.sender_email))
    
    def test_emailRecordAndEndPointCreated(self):
      er = EmailRecord()  
      er.sender = self.authUser
      er.save()
      message = SugarMessage(self.authUser, 'recipient@testcase.com',self.messenger, er)
      self.sendmail(message)
      defferred = message.eomReceived()
      defferred.addCallback(lambda check: self._assertEmailRecordSavedAndSingleEndPointCreated(er, 'recipient@testcase.com'))
    
    def _assertEmailRecordSavedAndSingleEndPointCreated(self, er, expectedRecipient):
      self.assertTrue(er.wasSaved)
      self.assertEquals(1, len(er.emailendpoint_set.all()))
      self.assertEquals(expectedRecipient, er.emailendpoint_set.all()[0].recipient)
    
    def test_endPointRecordCreatedForEachRecipient(self):
      er = EmailRecord() 
      er.sender = self.authUser 
      er.save()
      message = SugarMessage(self.authUser, 'recipient1@testcase.com',self.messenger, er)
      self.sendmail(message, to='recipient1@testcase.com,recipient2@testcase.com')
      deferred = message.eomReceived()
      deferred.addCallback(lambda check: self._test_endPointRecordCreatedForEachRecipient_part2(er))
      return deferred
      
    def _test_endPointRecordCreatedForEachRecipient_part2(self, er):
      message = SugarMessage(self.authUser, 'recipient2@testcase.com',self.messenger, er)
      self.sendmail(message, to='recipient1@testcase.com,recipient2@testcase.com')
      deferred = message.eomReceived()
      
      deferred.addCallback(lambda check: self._assertEndPointForEachRecipient(er, ['recipient1@testcase.com','recipient2@testcase.com']))
      return deferred
    
    def _assertEndPointForEachRecipient(self, er, recipients):
      endpoints = er.emailendpoint_set.all()
      self.assertEquals(len(recipients), len(endpoints))
      names = [endpoint.recipient for endpoint in endpoints]
      [self.assertTrue(name in names, "Missing endpoint for %s"%name) for name in recipients]
        
    def test_sendToRecipient(self):
      er = EmailRecord()  
      er.sender = self.authUser
      er.save()
      message = SugarMessage(self.authUser, 'recipient@testcase.com',self.messenger, er)
      self.sendmail(message, to="recipient@testcase.com")
      defferred = message.eomReceived()
      defferred.addCallback(lambda check: self.assertEquals(["recipient@testcase.com"],self.messenger.recipients))
    
    def test_messageIsIntact(self):
      er = EmailRecord()  
      er.sender = self.authUser
      er.save()
      message = SugarMessage(self.authUser, 'recipient@testcase.com',self.messenger, er)
      self.sendmail(message, text="Some body text")
      defferred = message.eomReceived()
      defferred.addCallback(lambda check: self.assertTrue("Some body text" in self.messenger.message))
      
class SugarMessageProcessorTestSuite(unittest.TestCase):
  def setUp(self):
    self.authUser = createUser("final@testcase.com","pass1")
  
  def test_FromHeaderReplaced(self):
    msg = MIMEText("Test")    
    msg['From'] = 'orginal@mailreceipts.com'
    newMessage = SugarMessageProcessor(self.authUser).process(msg,"category")
    
    self.assertEquals(self.authUser.email, newMessage["From"])
  
  def test_displayNameTransferred(self):
    msg = MIMEText("Test")    
    msg['From'] = 'Test <orginal@mailreceipts.com>'
    newMessage = SugarMessageProcessor(self.authUser).process(msg,"category")
    
    self.assertEquals("Test <%s>"%self.authUser.email, newMessage["From"])
  
  def test_nodisplayNameDoesNotFail(self):
    msg = MIMEText("Test")    
    msg['From'] = 'orginal@mailreceipts.com'
    newMessage = SugarMessageProcessor(self.authUser).process(msg,"category")
    
    self.assertEquals(self.authUser.email, newMessage["From"])
  
  def test_textMessagesConvertedToMultipart(self):
    msg = MIMEText("Test")    
    msg['From'] = 'orginal@mailreceipts.com'
    newMessage = SugarMessageProcessor(self.authUser).process(msg,"category")
    
    self.assertEquals('multipart/alternative', newMessage.get_content_type())
    self.assertEquals(2, len(newMessage.get_payload()))
  
  def test_textMessagesAreInjected(self):
    msg = MIMEText("Test")    
    msg['From'] = 'orginal@mailreceipts.com'
    newMessage = SugarMessageProcessor(self.authUser).process(msg,"category")
    
    self.assertEquals('multipart/alternative', newMessage.get_content_type())
    last_payload = newMessage.get_payload()[1]
    
    self.assertEquals('text/html', last_payload.get_content_type())
    self.assertTrue("</img>" in last_payload.get_payload())
  
  def test_htmlMessagesAreInjected(self):
    msg = MIMEText("<html><body>Test</body></html>",'html')    
    msg['From'] = 'orginal@mailreceipts.com'
    newMessage = SugarMessageProcessor(self.authUser).process(msg,"category")
    
    self.assertEquals('text/html', newMessage.get_content_type())
    self.assertTrue("</img>" in newMessage.get_payload())
  
  def test_multipartWithHtmlIsInjected(self):
    msg = MIMEMultipart('alternative')
    msg['From'] = 'orginal@mailreceipts.com'
    text = MIMEText("Test")    
    html = MIMEText("<html><body>Test</body></html>",'html')
    msg.attach(text)
    msg.attach(html)
    
    newMessage = SugarMessageProcessor(self.authUser).process(msg,"category")
    
    self.assertEquals(2, len(newMessage.get_payload()))
    self.assertTrue('</img>' in newMessage.get_payload()[1].get_payload())
      
  def test_multipartWithTextIsInjected(self):
    msg = MIMEMultipart('alternative')
    msg['From'] = 'orginal@mailreceipts.com'
    text1 = MIMEText("Test1")    
    text2 = MIMEText("Test2")
    msg.attach(text1)
    msg.attach(text2)
    
    newMessage = SugarMessageProcessor(self.authUser).process(msg,"category")
    
    self.assertEquals(3, len(newMessage.get_payload()))
    last_payload = newMessage.get_payload()[2]
    
    self.assertTrue('</img>' in last_payload.get_payload())
    self.assertTrue('Test2' in last_payload.get_payload())
  
  def test_AdvertisingFooterInjectedForNonPayingCusomter(self):
    msg = MIMEText("Test1") 
    msg['From'] = 'orginal@mailreceipts.com'
    
    profile = self.authUser.get_profile()
    profile.customer_level = CUSTOMER_LEVEL_FREE
    profile.save()
    newMessage = SugarMessageProcessor(self.authUser).process(msg,"category")
    
    self.assertEquals(2, len(newMessage.get_payload()))
    last_payload = newMessage.get_payload()[1]
    
    self.assertTrue('<img alt=\"Mail Receipts\"' in last_payload.get_payload())
  
  def test_AdvertisingFooterIsNotInjectedIntoPayingCustomer(self):
    msg = MIMEText("Test1") 
    msg['From'] = 'orginal@mailreceipts.com'
    
    profile = self.authUser.get_profile()
    profile.customer_level = CUSTOMER_LEVEL_FREE + 1
    profile.save()
    newMessage = SugarMessageProcessor(self.authUser).process(msg,"category")
    
    self.assertEquals(2, len(newMessage.get_payload()))
    last_payload = newMessage.get_payload()[1]
    
    self.assertFalse('<img alt=\"Mail Receipts\"' in last_payload.get_payload())
    
class RedirectMessageDeliveryTestSuite(unittest.TestCase):
  
  def setUp(self):
    self.messenger = RecordingMessenger()
  
  def test_validatesTrackerEmailAddresses(self):
    md = RedirectMessageDelivery(self.messenger)
    callback = md.validateTo('test-mailreceipts.com@tracker.mailreceipts.com')
    
  def test_convertsTrackerEmailToRedirectEmail(self):
    md = RedirectMessageDelivery(self.messenger)
    callback = md.validateTo('test-mailreceipts.com@tracker.mailreceipts.com')
    message = callback()
    self.assertEquals("test@mailreceipts.com", message.redirect)
    
  def test_failsForNonTrackerEmailAddresses(self):
    try:
      md = RedirectMessageDelivery(self.messenger)
      md.validateTo('test-mailreceipts.com@somethingtotallydifferent')
      self.fail("Expecting an SMTPBadRcpt")
    except smtp.SMTPBadRcpt:
      pass
  
class RedirectMessageTestSuite(unittest.TestCase):
  def setUp(self):
    self.messenger = RecordingMessenger()
  
  def sendmail(self, message,**kwargs):
        if "to" in kwargs:
            message.lineReceived("To: %s"%kwargs["to"])
        else:
            message.lineReceived("To: %s"%("default@testcase.com"))
            
        if "sender" in kwargs:
            message.lineReceived("From: %s"%kwargs["sender"])
        else:
            message.lineReceived("From: %s"%("default@testcase.com"))
            
        if "subject" in kwargs:
            message.lineReceived("Subject: %s"%kwargs["subject"])
        else:
            message.lineReceived("Subject: %s"%("default subject"))
        
        if "text" in kwargs:
            message.lineReceived(kwargs["text"])
        else:
            message.lineReceived("Default Text")
  
  def test_messageRedirected(self):
    message = RedirectMessage('redirect@mailreceipts.com',self.messenger)
    self.sendmail(message, to='original@testcase.com')
    deferred = message.eomReceived()
    deferred.addCallback(lambda check: self.assertEquals('redirect@mailreceipts.com',message["To"]))
    
    
if __name__ == '__main__':
    unittest.main()
    