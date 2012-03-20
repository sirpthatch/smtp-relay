# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
import email
import seed

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
msg['To'] = 'thatcher.clay@gmail.com'


# Send the message via our own SMTP server, but don't include the
# envelope header.
s = smtplib.SMTP('smtp.mailreceipts.com', 587) #'50.19.225.195')
s.ehlo()
s.starttls()
s.ehlo()
s.login('thatcher.clay@gmail.com','gho5u5')
#s.connect()

#s = smtplib.SMTP('smtp.mailreceipts.com',2500)
#s.login('thatcher.clay@gmail.com','greenmoose8')


#print(msg.as_string())
m = email.message_from_string(msg.as_string())
print(m.get_payload())
#s.sendmail('track@emailreceipts.com', ['thatcher@dropcapsule.com'], msg.as_string())
s.sendmail('thatcher.clay-gmail.com@tracker.mailreciepts.com', ['thatcher.clay@gmail.com'], msg.as_string())
s.quit()