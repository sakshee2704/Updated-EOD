# email_sender.py
import streamlit as st
import smtplib
from email.message import EmailMessage
import re
from config import SMTP_SERVER, SMTP_PORT # Import SMTP details from config

def send_email_report(content, today, sender_email, sender_password, recipient_emails):
    """
    Sends an email with the generated PDF report as an attachment.
    """
    msg = EmailMessage()
    msg['Subject'] = f"EOD Report - {content['name']} ({today})"
    msg['From'] = sender_email
    msg['To'] = ', '.join(recipient_emails)
    msg.set_content(f"Dear Manager,\n\nPlease find attached the End-of-Day banking report for {content['name']} ({content['branch']} Branch) for {today}.\n\nRegards,\nYour Reporting Team")
    msg.add_attachment(content['pdf_bytes'], maintype='application', subtype='pdf', filename=content['filename'])

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls() # Enable Transport Layer Security
        smtp.login(sender_email, sender_password) # Login with sender credentials
        smtp.send_message(msg) # Send the email

def validate_emails(emails_str):
    """
    Validates a comma-separated string of emails.
    Returns a list of valid emails or raises a ValueError if any are invalid.
    """
    valid_emails = []
    if not emails_str:
        return []

    emails_list = [e.strip() for e in emails_str.split(",") if e.strip()]
    if not emails_list:
        return []

    for email in emails_list:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError(f"Invalid email format: '{email}'")
        valid_emails.append(email)
    return valid_emails
