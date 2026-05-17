import os
import re
import smtplib
import ssl
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

smtp = os.getenv("SMTP", "smtp.mail.com")
port = int(os.getenv("PORT", 465))  # 465 for SMTP_SSL, 587 for STARTTLS
password = os.getenv("EMAIL_PASSWORD", "my_secret")
email = os.getenv("EMAIL_LOGIN", "test@mail.com")

file_adresses = os.getenv("FILE_ADDRESSES", "test.txt")
file_text = os.getenv("FILE_TEXT", "email_text_test.txt")

# Keep sender aligned with authenticated mailbox to satisfy strict policies.
sender_email = email

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")
SKIP_TOKENS = {"email", "e-mail", "emailadres", "emailaddress", "mail", "adres"}


def is_valid_email(address: str) -> bool:
    return bool(EMAIL_REGEX.fullmatch(address))


def load_recipients(path: str) -> list[str]:
    recipients: list[str] = []

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            # Skip empty lines and full-line comments
            if not line or line.startswith("#"):
                continue

            # Allow comma/semicolon separated values in one line
            parts = re.split(r"[;,]", line)

            for part in parts:
                address = part.strip().strip('"').strip("'")
                normalized = address.lower()

                if not address or normalized in SKIP_TOKENS:
                    continue

                if is_valid_email(address):
                    recipients.append(address)
                else:
                    print(f"Skipping invalid recipient entry: {address}")

    # Preserve order, remove duplicates
    return list(dict.fromkeys(recipients))


recipients = load_recipients(file_adresses)

if not recipients:
    raise ValueError(f"No valid recipient addresses found in '{file_adresses}'.")

context = ssl.create_default_context()

sent_count = 0
failed: list[str] = []

with smtplib.SMTP_SSL(smtp, port, context=context) as server:
    server.login(email, password)

    for receiver_email in recipients:
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = "test"
        msg.set_content(f"This is a test for {receiver_email}.")

        try:
            server.send_message(msg)
            sent_count += 1
            print(f"Email sent to {receiver_email}")
        except smtplib.SMTPRecipientsRefused as exc:
            failed.append(receiver_email)
            print(f"Recipient refused for {receiver_email}: {exc}")

print(f"Done. Sent {sent_count} email(s). Failed: {len(failed)}")
if failed:
    print("Failed recipients:", ", ".join(failed))
