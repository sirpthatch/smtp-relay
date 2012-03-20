from twisted.web.server import Site

import logging, logging.config
from plugins.tracker import settings
from plugins.tracker.requests import Tracker

logging.config.fileConfig(settings.TRACKER_LOGGING)


def main():
  from twisted.application import internet
  from twisted.application import service  
  
  root = Tracker()
  a = service.Application("Receipt Tracker Server")
  internet.TCPServer(settings.SPICE_TRACKER_PORT, Site(root)).setServiceParent(a)

  return a

application = main()