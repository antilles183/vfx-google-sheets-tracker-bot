import smtplib
from email.mime.text import MIMEText


def build_smtp(host: str, port: int, sender: str, app_password: str) -> smtplib.SMTP:
    server = smtplib.SMTP(host, port)
    server.starttls()
    server.login(sender, app_password)
    return server


def send_email(smtp: smtplib.SMTP, sender: str, to: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "html")
    msg["to"] = to
    msg["from"] = sender
    msg["subject"] = subject
    smtp.send_message(msg)
