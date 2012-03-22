import logging
import os
from core.relay.config import BasicConfiguration

DIR = os.path.abspath(os.path.dirname(__file__))
TRACKER_LOGGING = os.path.join(DIR,'logging.conf')

logging.config.fileConfig(TRACKER_LOGGING)




configuration = {
  "OUTBOUND_EMAIL_HOST":"...",
  "OUTBOUND_EMAIL_PORT":"...",
  "OUTBOUND_EMAIL_HOST_USER":"...",
  "OUTBOUND_EMAIL_HOST_PASSWORD":"...",

  "PROCESSORS":[],
  "AUDIENCE_FILTERS":{"to":[],
                      "from":[]},
  "AUTH_CHECKERS":[],

  "KEYS":{
      "PRIVATE":"",
      "PUBLIC":""
  },

  "NAME":"SMTP Tracking Relay Server",
  "PORTS":[25,587]
}
config = BasicConfiguration(configuration)

application = config.application()
