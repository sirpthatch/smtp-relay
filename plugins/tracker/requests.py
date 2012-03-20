from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor
from twisted.web import error
from twisted.python.filepath import FilePath
from twisted.web.static import File

from datetime import datetime, timedelta

import sys,os
sys.path.insert(0,os.getcwd()+"/output")
sys.path.insert(0,os.getcwd()+"/output/web")
os.environ['DJANGO_SETTINGS_MODULE'] = 'web.settings'

from calendar import calendar

from web.mailreceipts.models import EmailEndPoint, EmailRead
from core.alerts import send_alert

import logging

logger = logging.getLogger('spice')


class EmailTracker(Resource):
  def __init__(self, image):
    Resource.__init__(self)
    self.tracker_image = image
    
  def getChild(self, name, request):

    if not EmailEndPoint.objects.filter(category = name).exists():
      logger.info('Failed to find end point %s'%name)
      return ErrorTracker("Unknown id")
    ep = EmailEndPoint.objects.get(category = name)
    last_read_at = ep.read_at
    ep.read_at = datetime.now()
    ep.save()
    
    read = EmailRead()
    read.endpoint = ep
    read.user_agent = str(request.getHeader('user-agent'))
    read.ip_address = str(request.getClientIP())
    read.save()
    
    # Only resend an alert if they reopen it an hour after the last read
    if ep.flagged_for_alert and (last_read_at is None or (last_read_at is not None and ep.read_at - last_read_at < timedelta(hours=1))):
      send_alert(ep)
    
    return self.tracker_image

class ErrorTracker(Resource):
  def __init__(self, error):
    Resource.__init__(self)
    self.error = error
  def getChild(self):
    return self
  def render_GET(self, request):
    return "Error: "+str(error)
    
class UnknownTrackerType(Resource):
  def __init__(self, trackerType):
    Resource.__init__(self)
    self.trackerType = trackerType
  def getChild(self):
    return self
  def render_GET(self, request):
    logger.info('Failed to find tracker of type %s'%self.trackerType)
    
    return "Error: No resource with tracker type %s"%self.trackerType
    
class Tracker(Resource):
  
  def __init__(self):
    Resource.__init__(self)
    filepath = os.path.abspath(os.path.dirname(__file__))+"/a.png"
    self.tracker_image = File(filepath)
  
  def getChild(self, name, request):
    # Wishing I had python routes...
    # For now, assume a convention of {target}/{id}
    if (name.lower() == "email"):
      return EmailTracker(self.tracker_image)
    return UnknownTrackerType(name)
