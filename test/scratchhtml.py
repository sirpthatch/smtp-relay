import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
from email.mime.message import MIMEMessage
from email.message import Message
from email.mime.multipart import MIMEMultipart
import email
import seed

seed.createUser('testuser1@mailreceipts.com', 'pass')

html = """\
<html>
  <head></head>
  <body>
    <p>Hi!<br>
       How are you?<br>
       Here is the <a href="http://www.python.org">link</a> you wanted.
    </p>
  </body>
</html>
"""

msg = MIMEText(html, 'html')
msg['Subject'] = 'Subject line here'
msg['From'] = 'thatcher@emailreceipts.com'
msg['To'] = 'thatcher@dropcapsule.com'

# Send the message via our own SMTP server, but don't include the
# envelope header.
s = smtplib.SMTP('localhost',2500)
s.login('testuser1@mailreceipts.com','pass')

#print(msg.as_string())
m = email.message_from_string(msg.as_string())
print(m.get_payload())
s.sendmail('thatcher@emailreceipts.com', ['thatcher@dropcapsule.com'], msg.as_string())
s.quit()