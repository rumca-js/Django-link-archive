"""
    em = EmailReader("server")
    em.connect("username", "password")

    for email_data in em.get_emails():
        print("Subject:", email_data.title)
        print("From:", email_data.author)
        #print("Body:", email_data.body)

    em.close()
"""
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from email.utils import parseaddr


class Email(object):
    def __init__(self):
        self.title = None
        self.body = None
        self.date_published = None
        self.author = None
        self.id = None

    def __str__(self):
        return "{}/{}/{}\n{}".format(self.title, self.date_published, self.author, self.body)


class EmailReader(object):
    def __init__(self, server, time_limit=None, creds=None):
        """
        Specify time limit, to search only mails newer than time limit
        """
        self.server = server
        self.time_limit = time_limit
        self.method = "Simple"
        self.creds = creds

    def connect(self, username, password):
        self.imap = imaplib.IMAP4_SSL(self.server)
        if self.method == "Simple":
            return self.imap.login(username, password)
        elif self.method == "XOAUTH2":
            auth_string = self.generate_xoauth2_token(creds)
            return self.imap.authenticate("XOAUTH2", lambda x: auth_string)

    def generate_xoauth2_token(self, creds):
        return f"user={creds.id_token['email']}\1auth=Bearer {creds.token}\1\1"

    def get_emails(self):
        # Select the mailbox you want to read (in this case, the inbox)
        self.imap.select("inbox")

        # Search for all emails
        status, messages = self.imap.search(None, "ALL")
        email_ids = messages[0].split()
        email_ids.reverse()

        for email_data in self.read_emails_impl(email_ids):
            yield email_data

    def read_emails_impl(self, email_ids):
        for email_id in email_ids:
            mail = self.read_email_impl(email_id)
            if self.time_limit:
                if mail.date_published < self.time_limit:
                    break
                else:
                    yield mail

    def read_email_impl(self, email_id):
        # Fetch the email by ID
        res, msg_data = self.imap.fetch(email_id, "(RFC822)")
        raw_email = msg_data[0][1]

        msg = email.message_from_bytes(raw_email)
        mail = Email()
        mail.id = msg["Message-ID"]

        subject = self.decode_mime_words(msg["Subject"])

        body = None
        # Get the email body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                    except UnicodeDecodeError as E:
                        print("Cannot decode message body")
                    break
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except UnicodeDecodeError as E:
                print("Cannot decode message body")


        # Extract and parse the sent date
        date_header = msg["Date"]
        if date_header:
            #print("date_header")
            #print(date_header)
            try:
                mail.date_published = parsedate_to_datetime(date_header)
            except Exception as e:
                print(f"Failed to parse email date: {e}")
                mail.date_published = None
        else:
            mail.date_published = None

        mail.title = subject
        mail.body = body

        name, addr = parseaddr(msg["From"])
        decoded_name = self.decode_mime_words(name)
        mail.author = f"{decoded_name} <{addr}>" if decoded_name else addr

        return mail

    def decode_mime_words(self, header_value):
        if header_value is None:
            return ''
        decoded_fragments = decode_header(header_value)
        decoded_string = ''
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                try:
                    decoded_string += fragment.decode(encoding or 'utf-8', errors='replace')
                except Exception as e:
                    decoded_string += fragment.decode('utf-8', errors='replace')
            else:
                decoded_string += fragment
        return decoded_string

    def close(self):
        self.imap.logout()


if __name__ == "__main__":
    em = EmailReader("imap.poczta.onet.pl")
    em.connect("winstonarmanip@op.pl", "M@sakra8")

    for email_data in em.get_emails():
        print("Subject:", email_data.title)
        print("From:", email_data.author)
        print("Date published:", email_data.date_published)
        #print("Body:", email_data[2])

    em.close()
