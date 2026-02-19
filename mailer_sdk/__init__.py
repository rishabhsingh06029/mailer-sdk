"""
mailer-sdk
~~~~~~~~~~
A simple, production-ready Python SDK for sending emails via SMTP.

Supports Gmail, Outlook, and Yahoo out of the box.
Zero third-party dependencies — uses Python stdlib only.

Basic usage:
    >>> from mailer_sdk import Mailer
    >>> with Mailer(email='you@gmail.com', password='app-pass') as mailer:
    ...     mailer.send(to='friend@example.com', subject='Hi', body='Hello!')

Environment variable usage:
    $ export MAILER_EMAIL=you@gmail.com
    $ export MAILER_PASSWORD=your-app-password
    >>> with Mailer() as mailer:
    ...     mailer.send(to='friend@example.com', subject='Hi', body='Hello!')
"""

from .mailer import (
    Mailer,
    MailerException,
    AuthError,
    ConnectError,
    SendError,
    ValidationError,
)

__version__ = "1.0.2"
__author__  = "rishabh"
__email__   = "rishabhsingh06029@gmail.com"
__license__ = "MIT"

__all__ = [
    "Mailer",
    "MailerException",
    "AuthError",
    "ConnectError",
    "SendError",
    "ValidationError",
]
