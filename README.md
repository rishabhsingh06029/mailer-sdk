# 📧 mailer-sdk

> A simple, production-ready Python SDK for sending emails via SMTP.
> Zero dependencies. Gmail, Outlook, and Yahoo supported out of the box.

[![PyPI version](https://badge.fury.io/py/mailer-sdk.svg)](https://badge.fury.io/py/mailer-sdk)
[![Python](https://img.shields.io/pypi/pyversions/mailer-sdk.svg)](https://pypi.org/project/mailer-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Installation

```bash
pip install mailer-sdk
```

---

## Quick Start

```python
from mailer_sdk import Mailer

with Mailer(email="you@gmail.com", password="your-app-password") as mailer:
    mailer.send(
        to      = "friend@example.com",
        subject = "Hello!",
        body    = "Hey, this was sent using mailer-sdk!"
    )
```

---

## Environment Variables (Recommended)

Instead of hardcoding credentials, use environment variables:

```bash
export MAILER_EMAIL=you@gmail.com
export MAILER_PASSWORD=your-app-password
export MAILER_PROVIDER=gmail   # optional, default is gmail
```

```python
from mailer_sdk import Mailer

with Mailer() as mailer:   # reads from env automatically
    mailer.send(to="friend@example.com", subject="Hi", body="Hello!")
```

---

## Features

| Method              | Description                                   |
|---------------------|-----------------------------------------------|
| `send()`            | Send plain text or HTML email                 |
| `send_html()`       | Shortcut for HTML emails                      |
| `send_bulk()`       | Send individually to multiple recipients      |
| `send_template()`   | Send HTML with `{{placeholder}}` fill-in      |
| `send_with_retry()` | Auto-retry with exponential backoff           |

---

## Usage Examples

### Plain Text
```python
mailer.send(
    to      = "friend@example.com",
    subject = "Hello!",
    body    = "Plain text email."
)
```

### HTML Email
```python
mailer.send_html(
    to      = "friend@example.com",
    subject = "Welcome!",
    body    = "<h1>Hello!</h1><p>This is an <b>HTML</b> email.</p>"
)
```

### With CC, BCC, and Attachment
```python
mailer.send(
    to          = "friend@example.com",
    subject     = "Report",
    body        = "Please find the report attached.",
    cc          = ["manager@example.com"],
    bcc         = ["archive@example.com"],
    attachments = ["report.pdf"]
)
```

### Bulk Send
```python
result = mailer.send_bulk(
    recipients = ["a@example.com", "b@example.com", "c@example.com"],
    subject    = "Newsletter",
    body       = "Hello, here is this month's update!"
)
print(f"Sent {result['sent']}/{result['total']}")
```

### Template Email
```python
mailer.send_template(
    to       = "customer@example.com",
    subject  = "Order Confirmed",
    template = "<h2>Hi {{name}}!</h2><p>Order <b>#{{order_id}}</b> confirmed. Total: ${{total}}</p>",
    context  = {"name": "Alice", "order_id": "1042", "total": "59.99"}
)
```

### Retry on Failure
```python
mailer.send_with_retry(
    to          = "friend@example.com",
    subject     = "Important",
    body        = "Please read this.",
    max_retries = 3,   # default
    backoff     = 1    # 1s → 2s → 4s
)
```

---

## Supported Providers

| Provider  | Value      |
|-----------|------------|
| Gmail     | `"gmail"`  |
| Outlook   | `"outlook"`|
| Yahoo     | `"yahoo"`  |

```python
# Outlook example
mailer = Mailer(email="you@outlook.com", password="pass", provider="outlook")
```

---

## Gmail App Password Setup

Gmail requires an **App Password** (not your real password):

```
1. Go to → myaccount.google.com
2. Security → 2-Step Verification (enable it)
3. Security → App Passwords → Generate
4. Copy the 16-character password
5. Use it as your password above
```

---

## Error Handling

```python
from mailer_sdk import Mailer, AuthError, SendError, ConnectError, ValidationError

try:
    with Mailer(email="you@gmail.com", password="wrong-pass") as mailer:
        mailer.send(to="friend@example.com", subject="Hi", body="Hello!")

except AuthError as e:
    print(f"Auth failed [{e.code}]: {e.message}")    # bad credentials

except ConnectError as e:
    print(f"Can't connect [{e.code}]: {e.message}")  # server unreachable

except SendError as e:
    print(f"Send failed [{e.code}]: {e.message}")    # delivery failed

except ValidationError as e:
    print(f"Bad input [{e.code}]: {e.message}")      # invalid inputs
```

---

## Logging

Control SDK verbosity using Python's standard logging:

```python
import logging

# See all SDK activity
logging.getLogger("mailer_sdk").setLevel(logging.DEBUG)

# Quiet mode — only errors
logging.getLogger("mailer_sdk").setLevel(logging.ERROR)
```

---

## License

DT © Rishabh
