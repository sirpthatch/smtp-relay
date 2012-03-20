from twisted.cred.portal import IRealm
from twisted.cred.portal import Portal
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor
from twisted.mail.smtp import SMTPFactory
from twisted.cred import checkers

import sys,os

import logging, logging.config

from server.smtp import *
from server.tracker import Tracker
from common.config import settings 

logging.config.fileConfig('output-spice/server/runner/logging.conf')


def main():
  from twisted.application import internet
  from twisted.application import service  
  
  messenger = AuthenticatedMessenger(django_settings.OUTBOUND_EMAIL_HOST, 
                                       django_settings.OUTBOUND_EMAIL_PORT, 
                                       django_settings.OUTBOUND_EMAIL_HOST_USER, 
                                       django_settings.OUTBOUND_EMAIL_HOST_PASSWORD)
  
  root = Tracker()
  a = service.Application("Spice Server")
  internet.TCPServer(settings.SPICE_TRACKER_PORT, Site(root)).setServiceParent(a)
    
  portal = Portal(RedirectRealm(messenger = messenger))
  anonymousAccess = checkers.AllowAnonymousAccess()
  portal.registerChecker(anonymousAccess)
  internet.TCPServer(settings.SPICE_SMTP_PORT, SMTPFactory(portal)).setServiceParent(a)
  
  return a

application = main()