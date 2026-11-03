from unittest.mock import patch

import pytest

from src.services import email_service


def _configure_both_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(email_service.settings, "RESEND_API_KEY", "resend-test-key")
    monkeypatch.setattr(email_service.settings, "RESEND_FROM_EMAIL", "HVNH Hub <no-reply@example.test>")
    monkeypatch.setattr(email_service.settings, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(email_service.settings, "SMTP_USERNAME", "mailer@example.test")
    monkeypatch.setattr(email_service.settings, "SMTP_PASSWORD", "smtp-test-password")


def test_resend_is_primary_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_both_providers(monkeypatch)
    with patch.object(email_service.resend.Emails, "send") as send, \
         patch.object(email_service, "_send_smtp") as smtp:
        email_service._send_email("student@hvnh.edu.vn", "subject", "<p>body</p>")

    send.assert_called_once_with({
        "from": "HVNH Hub <no-reply@example.test>",
        "to": ["student@hvnh.edu.vn"],
        "subject": "subject",
        "html": "<p>body</p>",
    })
    smtp.assert_not_called()


def test_smtp_is_fallback_when_resend_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_both_providers(monkeypatch)
    with patch.object(email_service.resend.Emails, "send", side_effect=RuntimeError("provider unavailable")), \
         patch.object(email_service, "_send_smtp") as smtp:
        email_service._send_email("student@hvnh.edu.vn", "subject", "<p>body</p>")

    smtp.assert_called_once_with("student@hvnh.edu.vn", "subject", "<p>body</p>")


def test_failed_providers_return_safe_delivery_error(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_both_providers(monkeypatch)
    with patch.object(email_service.resend.Emails, "send", side_effect=RuntimeError("secret provider detail")), \
         patch.object(email_service, "_send_smtp", side_effect=email_service.EmailDeliveryError("smtp failure")):
        with pytest.raises(email_service.EmailDeliveryError, match="Không gửi được email"):
            email_service._send_email("student@hvnh.edu.vn", "subject", "<p>body</p>")

    assert "secret provider detail" not in caplog.text
    assert "student@hvnh.edu.vn" not in caplog.text
    assert any(getattr(record, "error_type", None) == "RuntimeError" for record in caplog.records)


def test_missing_providers_report_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(email_service.settings, "RESEND_API_KEY", "")
    monkeypatch.setattr(email_service.settings, "SMTP_HOST", "")
    monkeypatch.setattr(email_service.settings, "SMTP_USERNAME", "")
    monkeypatch.setattr(email_service.settings, "SMTP_PASSWORD", "")

    with pytest.raises(email_service.EmailDeliveryError, match="chưa được cấu hình"):
        email_service._send_email("student@hvnh.edu.vn", "subject", "<p>body</p>")
