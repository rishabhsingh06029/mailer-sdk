# Changelog

All notable changes to `mailer-sdk` will be documented here.

Format: [Semantic Versioning](https://semver.org)

---

## [1.0.0] — 2024-01-01

### Added
- Initial release
- `Mailer` class with Gmail, Outlook, Yahoo support
- `send()` — plain text and HTML emails
- `send_html()` — HTML shortcut
- `send_bulk()` — individual send to multiple recipients
- `send_template()` — `{{placeholder}}` HTML templates
- `send_with_retry()` — exponential backoff retry
- Context manager support (`with Mailer() as mailer`)
- Environment variable support (`MAILER_EMAIL`, `MAILER_PASSWORD`)
- Custom exceptions: `AuthError`, `ConnectError`, `SendError`, `ValidationError`
- Full type hints on all public methods
- Full docstrings on all public methods
- Zero third-party dependencies
