"""
Brevo sender. Sends one rendered email per subscriber via Brevo's transactional
API. Reuse the BREVO_API_KEY from your existing project.

Each send is independent and wrapped so one failed recipient doesn't abort the
rest. Failures are logged.
"""

import requests
import sys
from config import BREVO_API_KEY, SENDER_NAME, SENDER_EMAIL

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def send(to_email: str, to_name: str, subject: str, html: str) -> bool:
    if not BREVO_API_KEY:
        print("[send] No BREVO_API_KEY set; skipping send.", file=sys.stderr)
        return False
    try:
        resp = requests.post(
            BREVO_URL,
            headers={
                "api-key": BREVO_API_KEY,
                "content-type": "application/json",
                "accept": "application/json",
            },
            json={
                "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
                "to": [{"email": to_email, "name": to_name}],
                "subject": subject,
                "htmlContent": html,
            },
            timeout=30,
        )
        if resp.status_code >= 400:
            print(f"[send] FAILED -> {to_email}: HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
            return False
        print(f"[send] OK -> {to_email}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[send] FAILED -> {to_email}: {e}", file=sys.stderr)
        return False
