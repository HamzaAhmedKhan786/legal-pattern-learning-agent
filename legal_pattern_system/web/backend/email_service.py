from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send_email(*, to_email: str, subject: str, body: str) -> dict[str, str]:
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ.get("SMTP_USERNAME", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    from_email = os.environ.get("SMTP_FROM", username)
    if not host or not from_email:
        return {"status": "not_configured", "detail": "Set SMTP_HOST, SMTP_FROM, SMTP_USERNAME, and SMTP_PASSWORD."}

    message = EmailMessage()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)
    return {"status": "sent", "detail": f"Email sent to {to_email}"}
