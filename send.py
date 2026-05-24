import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SENDER_NAME, SENDER_EMAIL

SMTP_HOST = "smtp-relay.brevo.com"
SMTP_PORT = 587
SMTP_LOGIN = os.environ.get("BREVO_SMTP_LOGIN", "")
SMTP_KEY = os.environ.get("BREVO_SMTP_KEY", "")


def send(to_email, to_name, subject, html):
    if not (SMTP_LOGIN and SMTP_KEY):
        print("[send] No SMTP credentials set; skipping send.", file=sys.stderr)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_LOGIN, SMTP_KEY)
            server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())

        print(f"[send] OK -> {to_email}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[send] FAILED -> {to_email}: {e}", file=sys.stderr)
        return False
