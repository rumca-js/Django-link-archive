"""

em = EmailChecker()
em.connect()

for email_data in em.check_emails():
    print("Subject:", email_data[0])
    print("From:", email_data[1])
    #print("Body:", email_data[2])

em.close()
"""
import imaplib
import email
from email.header import decode_header


class EmailReader(object):
    def __init__(self, server):
        self.server = server

    def connect(self, username, password):
        self.imap = imaplib.IMAP4_SSL(self.server)
        self.imap.login(username, password)

    def check_emails(self):
        # Select the mailbox you want to read (in this case, the inbox)
        self.imap.select("inbox")

        # Search for all emails
        status, messages = self.imap.search(None, "ALL")
        email_ids = messages[0].split()

        for email_data in self.read_emails(email_ids):
            yield email_data

    def read_emails(self, email_ids):
        result = []

        for email_id in email_ids:
            yield self.read_email(email_id)

        return result

    def read_email(self, email_id):
        # Fetch the email by ID
        res, msg_data = self.imap.fetch(email_id, "(RFC822)")
        raw_email = msg_data[0][1]

        msg = email.message_from_bytes(raw_email)

        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8")

        body = None
        # Get the email body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()

        return [subject, msg["From"], body]

    def close(self):
        self.imap.logout()
