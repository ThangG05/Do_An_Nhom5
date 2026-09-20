import resend

from src.config import settings


class EmailDeliveryError(Exception):
    """Không thể chuyển email qua nhà cung cấp."""


def send_password_reset_code(email: str, code: str) -> None:
    if not settings.RESEND_API_KEY:
        raise EmailDeliveryError("Dịch vụ gửi email chưa được cấu hình.")
    resend.api_key = settings.RESEND_API_KEY
    try:
        resend.Emails.send({"from": settings.RESEND_FROM_EMAIL, "to": [email], "subject": "Mã khôi phục mật khẩu HVNH Hub", "html": f"<h2>Khôi phục mật khẩu HVNH Hub</h2><p>Mã của bạn:</p><p style='font-size:32px;font-weight:700;letter-spacing:8px'>{code}</p><p>Mã hết hạn sau {settings.OTP_EXPIRE_MINUTES} phút.</p>"})
    except Exception as exc:
        raise EmailDeliveryError("Không gửi được email khôi phục mật khẩu.") from exc


def send_verification_code(email: str, code: str) -> None:
    if not settings.RESEND_API_KEY:
        raise EmailDeliveryError("Dịch vụ gửi email chưa được cấu hình.")

    resend.api_key = settings.RESEND_API_KEY
    try:
        resend.Emails.send(
            {
                "from": settings.RESEND_FROM_EMAIL,
                "to": [email],
                "subject": "Mã xác thực tài khoản HVNH Hub",
                "html": (
                    "<div style='font-family:Arial,sans-serif;line-height:1.6'>"
                    "<h2>Xác thực tài khoản HVNH Hub</h2>"
                    "<p>Mã xác thực của bạn là:</p>"
                    f"<p style='font-size:32px;font-weight:700;letter-spacing:8px'>{code}</p>"
                    f"<p>Mã có hiệu lực trong {settings.OTP_EXPIRE_MINUTES} phút. "
                    "Không chia sẻ mã này với bất kỳ ai.</p>"
                    "</div>"
                ),
            }
        )
    except Exception as exc:
        raise EmailDeliveryError("Không gửi được email xác thực.") from exc
