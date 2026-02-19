import os
import smtplib
import logging
import time
from typing import Union, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)

PROVIDERS = {
    "gmail":   {"host": "smtp.gmail.com",      "port": 587},
    "outlook": {"host": "smtp.office365.com",  "port": 587},
    "yahoo":   {"host": "smtp.mail.yahoo.com", "port": 587},
}

# ── Custom Exceptions ──────────────────────────────────────────
class MailerException(Exception):
    """Base exception for all Mailer errors."""
    def __init__(self, code: int, message: str):
        self.code    = code
        self.message = message
        super().__init__(f"[{code}] {message}")

class AuthError(MailerException):
    """Raised when SMTP authentication fails."""
    pass

class ConnectError(MailerException):
    """Raised when connection to SMTP server fails."""
    pass

class SendError(MailerException):
    """Raised when email delivery fails."""
    pass

class ValidationError(MailerException):
    """Raised when input validation fails."""
    pass


# ── Mailer Class ───────────────────────────────────────────────
class Mailer:
    """
    A simple, production-ready SMTP email client.

    Supports Gmail, Outlook, and Yahoo out of the box.
    Credentials can be passed directly or via environment variables.

    Args:
        email    (str): Sender email address. Falls back to MAILER_EMAIL env var.
        password (str): App password. Falls back to MAILER_PASSWORD env var.
        provider (str): Email provider — 'gmail', 'outlook', 'yahoo'. Default: 'gmail'.
        timeout  (int): SMTP connection timeout in seconds. Default: 10.

    Example:
        >>> from mailer_sdk import Mailer
        >>> with Mailer(email='you@gmail.com', password='app-pass') as mailer:
        ...     mailer.send(to='friend@example.com', subject='Hi', body='Hello!')
    """

    __version__ = "1.0.0"

    def __init__(
        self,
        email   : Optional[str] = None,
        password: Optional[str] = None,
        provider: str = "gmail",
        timeout : int = 10,
    ):
        self.email    = email    or os.environ.get("MAILER_EMAIL")
        self.password = password or os.environ.get("MAILER_PASSWORD")
        self.provider = provider or os.environ.get("MAILER_PROVIDER", "gmail")
        self.timeout  = timeout
        self._conn    = None

        if not self.email or not self.password:
            raise ValidationError(400,
                "Email and password are required. "
                "Pass them directly or set MAILER_EMAIL and MAILER_PASSWORD env vars."
            )

        cfg = PROVIDERS.get(self.provider)
        if not cfg:
            raise ValidationError(400,
                f"Unknown provider '{self.provider}'. "
                f"Supported: {list(PROVIDERS.keys())}"
            )

        self.host = cfg["host"]
        self.port = cfg["port"]

    # ── Connection ─────────────────────────────────────────────

    def connect(self) -> "Mailer":
        """
        Open and authenticate an SMTP connection.

        Returns:
            Mailer: self (for chaining)

        Raises:
            AuthError:    If credentials are invalid.
            ConnectError: If the SMTP server is unreachable.

        Example:
            >>> mailer.connect()
        """
        if self._conn:
            return self  # idempotent — already connected

        try:
            logger.info("Connecting to %s:%s ...", self.host, self.port)
            self._conn = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            self._conn.ehlo()
            self._conn.starttls()
            self._conn.login(self.email, self.password)
            logger.info("Connected and authenticated: %s", self.host)
        except smtplib.SMTPAuthenticationError as e:
            raise AuthError(535, f"Authentication failed. Check your App Password. Detail: {e}")
        except smtplib.SMTPConnectError as e:
            raise ConnectError(500, f"Could not connect to {self.host}:{self.port}. Detail: {e}")
        except Exception as e:
            raise ConnectError(500, str(e))

        return self

    def disconnect(self) -> None:
        """Close the SMTP connection."""
        if self._conn:
            try:
                self._conn.quit()
                logger.info("Disconnected from %s", self.host)
            except Exception:
                pass
            finally:
                self._conn = None

   def send(self, to, subject, body, html=False, cc=None, bcc=None, attachments=None) -> dict:

    #  Validate BEFORE the try block — won't get swallowed
    if not to:
        raise ValidationError(400, "'to' address is required.")

    try:
        msg            = MIMEMultipart()
        msg["From"]    = self.email
        msg["To"]      = ", ".join(to) if isinstance(to, list) else to
        msg["Subject"] = subject
        if cc:  msg["Cc"]  = ", ".join(cc)
        if bcc: msg["Bcc"] = ", ".join(bcc)

        msg.attach(MIMEText(body, "html" if html else "plain"))

        for path in (attachments or []):
            with open(path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = path.split("/")[-1]
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)

        recipients = (
            (to if isinstance(to, list) else [to]) +
            (cc or []) + (bcc or [])
        )

        self._conn.sendmail(self.email, recipients, msg.as_string())
        logger.info("Email sent to: %s", recipients)
        return {"success": True, "to": recipients}

    except MailerException:
        raise  #  let our own exceptions bubble up untouched

    except Exception as e:
        logger.error("Send failed: %s", str(e))
        raise SendError(500, str(e))  # only wraps true unexpected errors
    # ── Helpers ────────────────────────────────────────────────

    def send_html(
        self,
        to     : Union[str, List[str]],
        subject: str,
        body   : str,
    ) -> dict:
        """
        Shortcut to send an HTML email.

        Args:
            to      (str | list): Recipient address(es).
            subject (str):        Subject line.
            body    (str):        HTML body string.

        Returns:
            dict: {'success': True, 'to': [...]}

        Example:
            >>> mailer.send_html(to='x@x.com', subject='Hi', body='<h1>Hello!</h1>')
        """
        return self.send(to, subject, body, html=True)

    def send_bulk(
        self,
        recipients: List[str],
        subject   : str,
        body      : str,
        html      : bool = False,
    ) -> dict:
        """
        Send the same email individually to multiple recipients.

        Args:
            recipients (list): List of email addresses.
            subject    (str):  Subject line.
            body       (str):  Email body.
            html       (bool): Set True if body is HTML. Default: False.

        Returns:
            dict: {'sent': 2, 'failed': 1, 'total': 3, 'details': [...]}

        Example:
            >>> mailer.send_bulk(['a@x.com', 'b@x.com'], 'News', 'Hello!')
        """
        results = []
        for recipient in recipients:
            try:
                result = self.send(to=recipient, subject=subject, body=body, html=html)
                results.append({"to": recipient, "success": True})
            except MailerException as e:
                results.append({"to": recipient, "success": False, "error": e.message})
                logger.warning("Bulk send failed for %s: %s", recipient, e.message)

        sent   = sum(1 for r in results if r["success"])
        failed = len(results) - sent
        logger.info("Bulk send complete: %d/%d sent", sent, len(recipients))
        return {
            "sent"   : sent,
            "failed" : failed,
            "total"  : len(recipients),
            "details": results,
        }

    def send_template(
        self,
        to      : Union[str, List[str]],
        subject : str,
        template: str,
        context : dict,
    ) -> dict:
        """
        Send an HTML email with {{placeholder}} substitution.

        Args:
            to       (str | list): Recipient address(es).
            subject  (str):        Subject line.
            template (str):        HTML string with {{key}} placeholders.
            context  (dict):       Values to substitute into the template.

        Returns:
            dict: {'success': True, 'to': [...]}

        Example:
            >>> mailer.send_template(
            ...     to='x@x.com',
            ...     subject='Order Confirmed',
            ...     template='<h1>Hi {{name}}!</h1><p>Order #{{id}} confirmed.</p>',
            ...     context={'name': 'Alice', 'id': '1042'}
            ... )
        """
        body = template
        for key, val in context.items():
            body = body.replace(f"{{{{{key}}}}}", str(val))
        return self.send_html(to, subject, body)

    def send_with_retry(
        self,
        to         : Union[str, List[str]],
        subject    : str,
        body       : str,
        html       : bool = False,
        max_retries: int  = 3,
        backoff    : int  = 1,
    ) -> dict:
        """
        Send an email with automatic retry on failure.

        Args:
            to          (str | list): Recipient address(es).
            subject     (str):        Subject line.
            body        (str):        Email body.
            html        (bool):       Set True if body is HTML. Default: False.
            max_retries (int):        Maximum retry attempts. Default: 3.
            backoff     (int):        Base backoff seconds (doubles each attempt). Default: 1.

        Returns:
            dict: {'success': True, 'to': [...]}
               or {'success': False, 'error': 'Max retries exceeded'}

        Example:
            >>> mailer.send_with_retry(to='x@x.com', subject='Hi', body='Hello!')
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.send(to, subject, body, html=html)
            except AuthError:
                raise  # don't retry auth failures — won't fix themselves
            except SendError as e:
                last_error = e
                wait = backoff * (2 ** attempt)  # 1s → 2s → 4s
                logger.warning(
                    "Attempt %d/%d failed. Retrying in %ds... (%s)",
                    attempt + 1, max_retries, wait, e.message
                )
                time.sleep(wait)

        return {"success": False, "error": f"Max retries ({max_retries}) exceeded. Last error: {last_error.message}"}

    # ── Representation ─────────────────────────────────────────

    def __repr__(self) -> str:
        masked = self.email[:4] + "****" if self.email else "None"
        return f"Mailer(email={masked}, provider={self.provider}, connected={self._conn is not None})"

    # ── Context Manager ────────────────────────────────────────

    def __enter__(self) -> "Mailer":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.disconnect()
        return False  # don't suppress exceptions
