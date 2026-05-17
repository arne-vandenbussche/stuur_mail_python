# stuur_mail_lmp

Simple Python script to send bulk emails via SMTP over SSL.

It supports:
- recipients loaded from a file
- plain text body from a file
- optional HTML body from a file (multipart email)
- basic recipient filtering/validation
- automatic reconnect + one retry when SMTP connection drops
- terminal logging and file logging
- output file with failed recipients

## Requirements

- Python 3.10+
- Package: `python-dotenv`

Install dependency:

```bash
pip install python-dotenv
```

## Project files

- `main.py` — main sender script
- `emailadressen.txt` / `test.txt` — recipient list examples
- `email_text.txt` / `mail_text_example.txt` — text body examples
- `email_html.html` / `mail_html_example.html` — HTML body examples
- `send_log.txt` — run log output (appended)
- `failed_recipients.txt` — failed recipients output (overwritten per run)

## Environment variables

Create a `.env` file in the project root, for example:

```env
SMTP=smtp.yourprovider.com
PORT=465
EMAIL_LOGIN=you@yourdomain.com
EMAIL_PASSWORD=your_password_or_app_password
SUBJECT=LMP uitnodiging

FILE_ADDRESSES=emailadressen.txt
FILE_TEXT=email_text.txt
FILE_HTML=email_html.html

FAILED_RECIPIENTS_FILE=failed_recipients.txt
SEND_LOG_FILE=send_log.txt
```

### Notes

- The script currently uses `SMTP_SSL` (typically port `465`).
- `From` is automatically aligned with `EMAIL_LOGIN`.
- If your provider requires app passwords (MFA enabled accounts), use an app password.

## Recipient file format

In `FILE_ADDRESSES`:
- one address per line, or multiple separated by `,` or `;`
- empty lines and lines starting with `#` are ignored
- duplicates are removed
- obvious headers like `emailadres` are ignored

Example:

```txt
# recipients
alice@example.com
bob@example.com; carol@example.com
```

## Message files

- `FILE_TEXT` is required and must not be empty.
- `FILE_HTML` is optional. If set, the email is sent as multipart with both text and HTML.

## Run

From the project folder:

```bash
python3 main.py
```

## Output behavior

- Successes and errors are printed to terminal.
- The same lines are appended to `SEND_LOG_FILE`.
- Failed recipients are written to `FAILED_RECIPIENTS_FILE` (one per line).

## Common issues

### SSL certificate verify failed
On macOS with Python from python.org, run the bundled certificate installer once ("Install Certificates.command").

### SMTP authentication failed (535)
Check SMTP host/port/security mode, username/password, and app-password requirements.

### Outlook/Office 365 sender policy rejection (5.7.x)
Ensure sender domain authentication is configured correctly (SPF/DKIM/DMARC alignment), and that the authenticated mailbox is allowed to send as the chosen From address.

## Security tips

- Never commit `.env` with real credentials.
- Prefer app passwords over account passwords where possible.
- Keep logs free of secrets (this script does not log passwords).
