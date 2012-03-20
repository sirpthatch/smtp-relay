from django.template import loader, Context
from mailreceipts.lib.mailer import Mailer
from mailreceipts.views import user_agent_string_from_endpoint
from django.conf import settings

def send_alert(endpoint):
  recipient = endpoint.recipient
  date_read = endpoint.read_at
  email_subject = endpoint.email.subject
  user_email = endpoint.email.sender.email
  
  subject = "%s opened your email"%(str(recipient))

  read_time = date_read.strftime("today (%m/%d/%Y) at %I:%M:%p")

  t = loader.get_template('mailreceipts/alert.html')
  c = Context({'BASE_URL' : settings.BASE_URL,
               'Reader' : recipient,
               'Subject' : email_subject,
               'Read_Time' : read_time,
               'email_address' : user_email,
               'user_agent' : user_agent_string_from_endpoint(endpoint)
              })
  html_content = t.render(c)
  text_content = "%s read your email \"%s\" %s"%(str(recipient), email_subject, read_time)
  msg = Mailer(subject, text_content, 'read-notification@mailreceipts.com', [user_email])
  msg.attach_alternative(html_content, "text/html")
  msg.send()