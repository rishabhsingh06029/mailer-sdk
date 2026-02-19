"""
Unit tests for mailer-sdk.
Run with: pytest tests/ -v
"""
import pytest
from unittest.mock import MagicMock, patch
from mailer_sdk import Mailer, AuthError, ConnectError, SendError, ValidationError


# ── Init Tests ─────────────────────────────────────────────────
class TestMailerInit:

    def test_init_with_credentials(self):
        m = Mailer(email="test@gmail.com", password="pass123")
        assert m.email    == "test@gmail.com"
        assert m.host     == "smtp.gmail.com"
        assert m.port     == 587
        assert m._conn    is None

    def test_init_from_env(self, monkeypatch):
        monkeypatch.setenv("MAILER_EMAIL",    "env@gmail.com")
        monkeypatch.setenv("MAILER_PASSWORD", "envpass")
        m = Mailer()
        assert m.email    == "env@gmail.com"
        assert m.password == "envpass"

    def test_init_missing_credentials_raises(self):
        with pytest.raises(ValidationError) as exc:
            Mailer()
        assert exc.value.code == 400

    def test_init_unknown_provider_raises(self):
        with pytest.raises(ValidationError):
            Mailer(email="x@x.com", password="pass", provider="unknown")

    def test_init_outlook_provider(self):
        m = Mailer(email="x@outlook.com", password="pass", provider="outlook")
        assert m.host == "smtp.office365.com"

    def test_repr_masks_email(self):
        m = Mailer(email="test@gmail.com", password="pass")
        assert "****" in repr(m)
        assert "test" in repr(m)


# ── Connect Tests ──────────────────────────────────────────────
class TestMailerConnect:

    @patch("smtplib.SMTP")
    def test_connect_success(self, mock_smtp):
        mock_conn = MagicMock()
        mock_smtp.return_value = mock_conn

        m = Mailer(email="test@gmail.com", password="pass")
        result = m.connect()

        assert result is m                  # returns self
        mock_conn.ehlo.assert_called_once()
        mock_conn.starttls.assert_called_once()
        mock_conn.login.assert_called_once_with("test@gmail.com", "pass")

    @patch("smtplib.SMTP")
    def test_connect_idempotent(self, mock_smtp):
        mock_conn = MagicMock()
        mock_smtp.return_value = mock_conn

        m = Mailer(email="test@gmail.com", password="pass")
        m.connect()
        m.connect()  # second call should be no-op

        assert mock_smtp.call_count == 1    # SMTP() called only once

    @patch("smtplib.SMTP")
    def test_connect_auth_error(self, mock_smtp):
        import smtplib
        mock_conn = MagicMock()
        mock_conn.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        mock_smtp.return_value = mock_conn

        m = Mailer(email="test@gmail.com", password="wrong")
        with pytest.raises(AuthError) as exc:
            m.connect()
        assert exc.value.code == 535


# ── Send Tests ─────────────────────────────────────────────────
class TestMailerSend:

    def _mailer_with_mock_conn(self):
        m = Mailer(email="test@gmail.com", password="pass")
        m._conn = MagicMock()
        return m

    def test_send_plain_text(self):
        m = self._mailer_with_mock_conn()
        result = m.send(to="friend@x.com", subject="Hi", body="Hello")
        assert result["success"] is True
        assert "friend@x.com" in result["to"]

    def test_send_html(self):
        m = self._mailer_with_mock_conn()
        result = m.send_html(to="friend@x.com", subject="Hi", body="<h1>Hi</h1>")
        assert result["success"] is True

    def test_send_missing_to_raises(self):
        m = self._mailer_with_mock_conn()
        with pytest.raises(ValidationError):
            m.send(to="", subject="Hi", body="Hello")

    def test_send_to_list(self):
        m = self._mailer_with_mock_conn()
        result = m.send(to=["a@x.com", "b@x.com"], subject="Hi", body="Hello")
        assert result["success"] is True
        assert len(result["to"]) == 2

    def test_send_bulk(self):
        m = self._mailer_with_mock_conn()
        result = m.send_bulk(
            recipients=["a@x.com", "b@x.com", "c@x.com"],
            subject="Hi", body="Hello"
        )
        assert result["sent"]  == 3
        assert result["total"] == 3

    def test_send_template(self):
        m = self._mailer_with_mock_conn()
        result = m.send_template(
            to="x@x.com", subject="Hi",
            template="Hello {{name}}, order #{{id}}",
            context={"name": "Alice", "id": "42"}
        )
        assert result["success"] is True

    def test_send_with_retry_succeeds(self):
        m = self._mailer_with_mock_conn()
        result = m.send_with_retry(to="x@x.com", subject="Hi", body="Hello")
        assert result["success"] is True

    def test_send_with_retry_exhausted(self):
        m = self._mailer_with_mock_conn()
        m._conn.sendmail.side_effect = Exception("SMTP error")
        result = m.send_with_retry(
            to="x@x.com", subject="Hi", body="Hello",
            max_retries=2, backoff=0  # backoff=0 so tests don't sleep
        )
        assert result["success"] is False
        assert "retries" in result["error"]


# ── Context Manager Tests ──────────────────────────────────────
class TestContextManager:

    @patch("smtplib.SMTP")
    def test_context_manager_connects_and_disconnects(self, mock_smtp):
        mock_conn = MagicMock()
        mock_smtp.return_value = mock_conn

        with Mailer(email="test@gmail.com", password="pass") as m:
            assert m._conn is not None

        mock_conn.quit.assert_called_once()
