import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.MIMEBase import MIMEBase
import email
from email import Encoders
import seed
import os

seed.createUser('testuser1@mailreceipts.com', 'pass')

msg = MIMEMultipart('mixed')
msg['Subject'] = 'Subject line here'
msg['From'] = 'thatcher@emailreceipts.com'
msg['To'] = 'thatcher@dropcapsule.com'

# Create the body of the message (a plain-text and an HTML version).
text = "Hi!\nHow are you?\nHere is the link you wanted:\nhttp://www.python.org"
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

DIRNAME = os.path.abspath(os.path.dirname(__file__))
file = DIRNAME+"/scratch.py"

part1 = MIMEText(text, 'plain')
#part1 = MIMEText(html, 'html')
part2 = MIMEBase('application', "octet-stream")
part2.set_payload( open(file,"rb").read() )
Encoders.encode_base64(part2)
part2.add_header('Content-Disposition', 'attachment; filename="%s"'% os.path.basename(file))

# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
msg.attach(part1)
msg.attach(part2)

# Send the message via our own SMTP server, but don't include the
# envelope header.
s = smtplib.SMTP('localhost',2500)
s.login('testuser1@mailreceipts.com','pass')

#print(msg.as_string())
m = email.message_from_string(msg.as_string())
print(m.get_payload())
s.sendmail('thatcher@emailreceipts.com', ['thatcher@dropcapsule.com'], msg.as_string())
s.quit()