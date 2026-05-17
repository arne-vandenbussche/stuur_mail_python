import os
import re
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

smtp = os.getenv("SMTP", "smtp.mail.com")
port = int(os.getenv("PORT", 465))  # 465 for SMTP_SSL, 587 for STARTTLS
password = os.getenv("EMAIL_PASSWORD", "my_secret")
email = os.getenv("EMAIL_LOGIN", "test@mail.com")
subject = os.getenv("SUBJECT", "zomaar een mail")

file_adresses = os.getenv("FILE_ADDRESSES", "test.txt")
file_text = os.getenv("FILE_TEXT", "message.txt")
file_html = os.getenv("FILE_HTML", "")
failed_recipients_file = os.getenv("FAILED_RECIPIENTS_FILE", "failed_recipients.txt")
send_log_file = os.getenv("SEND_LOG_FILE", "send_log.txt")

# Keep sender aligned with authenticated mailbox to satisfy strict policies.
sender_email = email

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")
SKIP_TOKENS = {"email", "e-mail", "emailadres", "emailaddress", "mail", "adres"}


def is_valid_email(address: str) -> bool:
    return bool(EMAIL_REGEX.fullmatch(address))


def load_message(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        message = f.read().strip()

    if not message:
        raise ValueError(f"Message file '{path}' is empty.")

    return message


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


message_body = load_message(file_text)
html_body = load_message(file_html) if file_html else None
recipients = load_recipients(file_adresses)

if not recipients:
    raise ValueError(f"No valid recipient addresses found in '{file_adresses}'.")

context = ssl.create_default_context()

sent_count = 0
sent_recipients: list[str] = []
failed: list[str] = []


def log(message: str, log_handle) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    line = f"[{timestamp}] {message}"
    print(line)
    log_handle.write(line + "\n")
    log_handle.flush()


def connect_server() -> smtplib.SMTP_SSL:
    server = smtplib.SMTP_SSL(smtp, port, context=context)
    server.login(email, password)
    return server


with open(send_log_file, "a", encoding="utf-8") as send_log:
    log("--- Start mail send session ---", send_log)
    server = None

    try:
        server = connect_server()
        log("Connected and authenticated to SMTP server.", send_log)

        for receiver_email in recipients:
            msg = EmailMessage()
            msg["From"] = sender_email
            msg["To"] = receiver_email
            msg["Subject"] = subject
            msg.set_content(message_body)

            if html_body:
                msg.add_alternative(html_body, subtype="html")

            try:
                server.send_message(msg)
                sent_count += 1
                sent_recipients.append(receiver_email)
                log(f"Email sent to {receiver_email}", send_log)
            except smtplib.SMTPRecipientsRefused as exc:
                failed.append(receiver_email)
                log(f"Recipient refused for {receiver_email}: {exc}", send_log)
            except (smtplib.SMTPServerDisconnected, ssl.SSLError, OSError) as exc:
                log(f"Connection issue while sending to {receiver_email}: {exc}", send_log)
                log("Reconnecting and retrying once...", send_log)

                try:
                    if server is not None:
                        server.quit()
                except Exception:
                    pass

                try:
                    server = connect_server()
                    server.send_message(msg)
                    sent_count += 1
                    sent_recipients.append(receiver_email)
                    log(f"Email sent to {receiver_email} (after reconnect)", send_log)
                except smtplib.SMTPRecipientsRefused as retry_exc:
                    failed.append(receiver_email)
                    log(f"Recipient refused for {receiver_email} after reconnect: {retry_exc}", send_log)
                except smtplib.SMTPException as retry_exc:
                    failed.append(receiver_email)
                    log(f"SMTP error for {receiver_email} after reconnect: {retry_exc}", send_log)
                except Exception as retry_exc:
                    failed.append(receiver_email)
                    log(f"Unexpected error for {receiver_email} after reconnect: {retry_exc}", send_log)
            except smtplib.SMTPException as exc:
                failed.append(receiver_email)
                log(f"SMTP error for {receiver_email}: {exc}", send_log)

    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                pass

    with open(failed_recipients_file, "w", encoding="utf-8") as f:
        for receiver_email in failed:
            f.write(receiver_email + "\n")

    log(f"Done. Sent {sent_count} email(s). Failed: {len(failed)}", send_log)
    log(f"Failed recipients written to {failed_recipients_file}", send_log)
    log(f"Successfully sent recipients are logged in {send_log_file}", send_log)
    log("--- End mail send session ---", send_log)
