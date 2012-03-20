from twisted.application import internet
from twisted.cred.portal import IRealm
from twisted.cred.portal import Portal
from twisted.mail import smtp
from twisted.internet.ssl import PrivateCertificate
from twisted.internet.protocol import ServerFactory
from twisted.internet import ssl
from twisted.protocols.tls import TLSMemoryBIOFactory

import sys,os
from server.smtp import *
from server import settings

import logging, logging.config
logging.config.fileConfig('output-sugar/server/runner/logging.conf')


def main():
  from twisted.application import internet
  from twisted.application import service

  messenger = AuthenticatedMessenger(django_settings.OUTBOUND_EMAIL_HOST,
                                     django_settings.OUTBOUND_EMAIL_PORT,
                                     django_settings.OUTBOUND_EMAIL_HOST_USER,
                                     django_settings.OUTBOUND_EMAIL_HOST_PASSWORD)

  portal = Portal(SugarRealm(messenger = messenger))
  checker = DjangoAuthChecker()
  portal.registerChecker(checker)

  secureContextFactory = ssl.DefaultOpenSSLContextFactory(
          'output-sugar/sugar.private.pem',
          'output-sugar/sugar.public.pem'
          )

  sugarFactory = SugarSMTPFactory(portal,secureContextFactory)

  a = service.Application("SMTP Relay Server")
  internet.TCPServer(settings.SUGAR_SMTP_PORT, sugarFactory).setServiceParent(a)
  internet.TCPServer(settings.SUGAR_SMTP_PORT_SECURE, sugarFactory).setServiceParent(a)

  return a

application = main()