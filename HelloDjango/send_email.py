import os
import smtplib
import sys
from configparser import ConfigParser
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate


def send_email(subject, body_text, to_emails=None, cc_emails=None, bcc_emails=None, files_to_attach=None):
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "email_config.ini")

    if os.path.exists(config_path):
        cfg = ConfigParser()
        cfg.read(config_path)
    else:
        sys.exit(1)

    if to_emails is None:
        to_emails = cfg.get("smtp", "receiver")
    if bcc_emails is None:
        bcc_emails = cfg.get("smtp", "cc_receiver")
    if cc_emails is None:
        cc_emails = cfg.get("smtp", "bcc_receiver")

    server = cfg.get("smtp", "server")
    port = cfg.get("smtp", "port")
    sender = cfg.get("smtp", "sender")
    password = cfg.get("smtp", "password")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)

    if body_text:
        msg.attach(MIMEText(body_text))

    msg["To"] = ', '.join((to_emails,))
    msg["cc"] = ', '.join((cc_emails,))
    msg["bcc"] = ', '.join((bcc_emails,))

    if files_to_attach is not None:
        for file_to_attach in files_to_attach:
            header = 'Content-Disposition', 'attachment; filename="%s"' % file_to_attach
            attachment = MIMEBase('application', "octet-stream")

            try:
                with open(file_to_attach, "rb") as fh:
                    data = fh.read()
                attachment.set_payload(data)
                encoders.encode_base64(attachment)
                attachment.add_header(*header)
                msg.attach(attachment)
            except IOError:
                pass
#                sys.exit(1)
    mail = smtplib.SMTP(server, port)
    mail.starttls()
    mail.login(sender, password)

    mail.sendmail(sender, [to_emails, cc_emails, bcc_emails], msg.as_string())
    mail.quit()
