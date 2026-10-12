from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from src.api.endpoints import feedback
from src.services import email_service


def test_feedback_uses_authenticated_identity(monkeypatch):
    sender = Mock()
    monkeypatch.setattr(feedback, "consume", lambda *_: (True, 0))
    monkeypatch.setattr(feedback, "send_user_feedback", sender)
    user = Mock(id="user-id", email="student@hvnh.edu.vn", username="student")
    user.profile.full_name = "Sinh viên A"

    result = feedback.submit_feedback(feedback.FeedbackRequest(message="Góp ý hợp lệ"), user, Mock())

    assert result["message"]
    sender.assert_called_once_with(sender_email="student@hvnh.edu.vn", sender_name="Sinh viên A", message="Góp ý hợp lệ")


def test_feedback_does_not_report_success_when_mail_fails(monkeypatch):
    monkeypatch.setattr(feedback, "consume", lambda *_: (True, 0))
    monkeypatch.setattr(feedback, "send_user_feedback", lambda **_: (_ for _ in ()).throw(email_service.EmailDeliveryError("SMTP offline")))
    user = Mock(id="user-id", email="student@hvnh.edu.vn", username="student")
    user.profile = None

    with pytest.raises(HTTPException) as error:
        feedback.submit_feedback(feedback.FeedbackRequest(message="Góp ý hợp lệ"), user, Mock())

    assert error.value.status_code == 503


def test_feedback_email_escapes_untrusted_content(monkeypatch):
    sent = []
    monkeypatch.setattr(email_service.settings, "FEEDBACK_TO_EMAIL", "support@example.test")
    monkeypatch.setattr(email_service, "_send_email", lambda *args: sent.append(args))

    email_service.send_user_feedback(
        sender_email="student@hvnh.edu.vn",
        sender_name="<Student>",
        message="Dòng đầu\n<script>alert(1)</script>",
    )

    assert sent[0][0] == "support@example.test"
    assert "THÔNG TIN NGƯỜI GỬI" in sent[0][2]
    assert "NỘI DUNG GÓP Ý" in sent[0][2]
    assert "mailto:student@hvnh.edu.vn" in sent[0][2]
    assert "Dòng đầu<br>&lt;script&gt;" in sent[0][2]
    assert "&lt;Student&gt;" in sent[0][2]
    assert "&lt;script&gt;" in sent[0][2]
    assert "<script>" not in sent[0][2]
