"""SMTP transport choices and Indonesian email content without external delivery."""

import uuid
from decimal import Decimal

import pytest

from app.config import Settings
from app.services.mailer import GradeEmail, send_grade_email, validate_address


@pytest.mark.parametrize("security", ["starttls", "ssl", "none"])
def test_smtp_transport_and_grade_content(monkeypatch, security):
    calls = []
    settings = Settings(_env_file=None, smtp_host="smtp.example.com", smtp_port=587,
                        smtp_user="sender@example.com", smtp_password="test-only-password",
                        smtp_from="sender@example.com", smtp_security=security, smtp_timeout=2)
    monkeypatch.setattr("app.services.mailer.get_settings", lambda: settings)

    class SMTP:
        def __init__(self, host, port, **kwargs):
            calls.append(("connect", host, port, kwargs))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            calls.append(("close",))

        def starttls(self, *, context):
            assert context.check_hostname
            calls.append(("tls",))

        def login(self, username, password):
            assert username == settings.smtp_user and password == settings.smtp_password
            calls.append(("login",))

        def send_message(self, message):
            calls.append(("message", message))

    monkeypatch.setattr("app.services.mailer.smtplib.SMTP_SSL" if security == "ssl" else "app.services.mailer.smtplib.SMTP", SMTP)
    send_grade_email(GradeEmail(uuid.uuid4(), "student@example.com", "Mahasiswa", "Basis\nData", "A", Decimal("44.99"), 2))
    assert calls[0][1:3] == ("smtp.example.com", 587)
    assert calls[0][3]["timeout"] == 2
    assert ("context" in calls[0][3]) == (security == "ssl")
    assert (("tls",) in calls) == (security == "starttls")
    assert ("login",) in calls and calls[-1] == ("close",)
    message = next(call[1] for call in calls if call[0] == "message")
    assert str(message["Subject"]) == "Nilai Basis Data telah dirilis"
    assert str(message["To"]) == "student@example.com"
    assert str(message["From"]) == "sender@example.com"
    assert "44.99" in message.get_content() and "Tidak lulus" in message.get_content()
    assert "Peringkat kelas: 2" in message.get_content()


@pytest.mark.parametrize("value", [None, "", "invalid", "a@invalid", "a@example.com\r\nBcc: other@example.com"])
def test_invalid_recipient_is_rejected(value):
    with pytest.raises(ValueError):
        validate_address(value)
