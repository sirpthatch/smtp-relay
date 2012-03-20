# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
import email
import seed

seed.createUser('thatcher.clay@gmail.com', 'pass')

# Open a plain text file for reading.  For this example, assume that
# the text file contains only ASCII characters.
# Create a text/plain message
msg = MIMEText("When will you get the server to work?!")

# me == the sender's email address
# you == the recipient's email address
#msg['Subject'] = 'Subject line here'
#msg['From'] = 'thatcher@emailreceipts.com'
#msg['To'] = 'thatcher@dropcapsule.com'

msg['Subject'] = 'Hey there'
msg['From'] = 'Thatcher <thatcher@mailreceipts.com>'
msg['To'] = 'sirpthatch-yaho.com@tracker.mailreceipts.com'


# Send the message via our own SMTP server, but don't include the
# envelope header.
#s = smtplib.SMTP('smtp.mailreceipts.com',587)
s = smtplib.SMTP('localhost',2501)

#s = smtplib.SMTP('smtp.mailreceipts.com',2500)
#s.login('thatcher.clay@gmail.com','greenmoose8')


#print(msg.as_string())
m = email.message_from_string(msg.as_string())
print(m.get_payload())
#s.sendmail('track@emailreceipts.com', ['thatcher@dropcapsule.com'], msg.as_string())
s.sendmail('t@d.com', ['sirpthatch-yahoo.com@tracker.mailreceipts.com'], msg.as_string())
s.quit()