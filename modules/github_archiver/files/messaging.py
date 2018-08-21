#!/usr/bin/env python3

import email.utils
import email.header
import email
import smtplib
import uuid
import time
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def uniaddr(addr):
    """ Unicode-format an email address """
    bits = email.utils.parseaddr(addr)
    return email.utils.formataddr((email.header.Header(bits[0], 'utf-8').encode(), bits[1]))

def mail(
        host = 'localhost',
        link = None,
        sender = "GitBox <gitbox@apache.org>",
        recipient = None,
        recipients = None,
        subject = '(Subject missing)',
        message = None,
        messageid = None
        ):
    """ Send an email, with all the unicode trimmings """
    # Optional metadata first
    if not messageid:
        messageid = email.utils.make_msgid("gitbox")
    date = email.utils.formatdate()

    # Now the required bits
    recipients = recipient or recipients # We accept both names, 'cause
    if not recipients:
        raise Exception("No recipients specified for email, can't send!")
    # We want this as a list
    if type(recipients) is str:
        recipients = [recipients]

    # py 2 vs 3 conversion
    if type(sender) is bytes:
        sender = sender.decode('utf-8', errors='replace')
    if type(message) is bytes:
        message = message.decode('utf-8', errors='replace')
    for i, rec in enumerate(recipients):
        if type(rec) is bytes:
            rec = rec.decode('utf-8', errors='replace')
            recipients[i] = rec

    # Recipient, Subject and Sender might be unicode.
    subject_encoded = email.header.Header(subject, 'utf-8')
    sender_encoded = uniaddr(sender)
    recipient_encoded = ", ".join([uniaddr(x) for x in recipients])

    if not message:
        raise Exception("No message body provided!")
    msg = MIMEMultipart()
    if link:
        msg['References'] = link
    msg['Subject'] = subject
    msg['To'] = recipient_encoded
    msg['From'] = sender_encoded
    msg['Message-ID'] = messageid
    msg['Date'] = date
    mtxt = MIMEText(message, 'plain')
    mtxt['Content-Type'] = "text/plain; charset=utf-8"

    msg.attach(mtxt)
    smtpObj = smtplib.SMTP(host)
    # Note that we're using the raw sender here...
    smtpObj.send_message(msg)
