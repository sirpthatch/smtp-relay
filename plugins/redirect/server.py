import logging
from core.relay.config import BasicConfiguration
import os, sys

DIR = os.path.abspath(os.path.dirname(__file__))

logging.config.fileConfig(os.path.join(DIR,'logging.conf'))
logger = logging.logger("smtprelay")

'''
  Add some logic to redirect emails going to
  a user
'''
def redirect_to(user):
  unprocessed_email_address, domain = str(user).split("@")
  username, realdomain = unprocessed_email_address.split('-')

  # Handle yahoo as the exception, they do not allow "yahoo" to appear in the username for an email address
  if realdomain.lower() == 'yaho.com':
    realdomain = 'yahoo.com'

  redirect_email = "%s@%s"%(username, realdomain)
  logger.info("Sending redirected message to %s"%redirect_email)

  return redirect_email

'''
  Start the configuration
'''
configuration = {
  "OUTBOUND_EMAIL_HOST":"...",
  "OUTBOUND_EMAIL_PORT":"...",
  "OUTBOUND_EMAIL_HOST_USER":"...",
  "OUTBOUND_EMAIL_HOST_PASSWORD":"...",

  "AUDIENCE_FILTERS":{"to":[redirect_to],
                      "from":[]},

  "NAME":"SMTP Redirect Relay Server",
  "PORTS":[25,587]
}
config = BasicConfiguration(configuration)

application = config.application()
