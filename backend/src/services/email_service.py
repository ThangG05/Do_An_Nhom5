import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import resend

from src.config import settings


class EmailDeliveryError(Exception):
    """Không thể chuyển email qua nhà cung cấp."""


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD)


def _send_smtp(email: str, subject: str, body_html: str) -> None:
    sender = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.SMTP_SENDER_NAME} <{sender}>"
    message["To"] = email
    message.attach(MIMEText(body_html, "html", "utf-8"))
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(sender, [email], message.as_string())
    except (OSError, smtplib.SMTPException) as exc:
        raise EmailDeliveryError("Không gửi được email xác thực qua SMTP.") from exc


def _send_email(email: str, subject: str, body_html: str) -> None:
    if _smtp_configured():
        _send_smtp(email, subject, body_html)
        return
    if not settings.RESEND_API_KEY:
        raise EmailDeliveryError("Dịch vụ gửi email chưa được cấu hình.")
    resend.api_key = settings.RESEND_API_KEY
    try:
        resend.Emails.send({"from": settings.RESEND_FROM_EMAIL, "to": [email], "subject": subject, "html": body_html})
    except Exception as exc:
        raise EmailDeliveryError("Không gửi được email.") from exc


def _otp_template(*, title: str, intro: str, code: str, expiry_minutes: int, note: str) -> str:
    safe_code = html.escape(code)
    return f"""<!doctype html>
<html lang="vi">
  <body style="margin:0;background:#f3f6fb;color:#17365d;font-family:Arial,Helvetica,sans-serif;">
    <div style="padding:32px 12px;">
      <div style="max-width:560px;margin:0 auto;background:#ffffff;border:1px solid #dce5f0;border-radius:18px;overflow:hidden;box-shadow:0 8px 24px rgba(16,54,92,.08);">
        <div style="background:#062f61;padding:26px 32px;color:#ffffff;">
          <div style="font-size:13px;letter-spacing:1.8px;font-weight:700;text-transform:uppercase;">HVNH HUB</div>
          <div style="font-size:25px;font-weight:700;margin-top:8px;">{html.escape(title)}</div>
        </div>
        <div style="padding:32px;">
          <p style="font-size:16px;line-height:1.65;margin:0 0 18px;">Xin chào,</p>
          <p style="font-size:16px;line-height:1.65;margin:0 0 24px;">{html.escape(intro)}</p>
          <div style="text-align:center;background:#f0f6ff;border:1px solid #cfe0f7;border-radius:14px;padding:22px 16px;margin:0 0 24px;">
            <div style="font-size:12px;color:#5c7390;letter-spacing:1.5px;text-transform:uppercase;font-weight:700;">MÃ XÁC THỰC</div>
            <div style="font-size:38px;line-height:1.2;letter-spacing:10px;color:#062f61;font-weight:800;margin:12px 0 4px;padding-left:10px;">{safe_code}</div>
            <div style="font-size:13px;color:#60758d;">Có hiệu lực trong {expiry_minutes} phút</div>
          </div>
          <div style="background:#fff8e8;border-left:4px solid #f0b429;border-radius:8px;padding:13px 15px;color:#6f5315;font-size:14px;line-height:1.55;">{html.escape(note)}</div>
          <p style="font-size:14px;line-height:1.6;color:#60758d;margin:24px 0 0;">Nếu bạn không yêu cầu thao tác này, hãy bỏ qua email và đổi mật khẩu nếu nghi ngờ tài khoản bị truy cập trái phép.</p>
        </div>
        <div style="border-top:1px solid #e7edf5;padding:18px 32px;color:#7890aa;font-size:12px;line-height:1.6;">
          Email tự động từ HVNH Hub.<br/>Vui lòng không trả lời email này.
        </div>
      </div>
    </div>
  </body>
</html>"""


def send_password_reset_code(email: str, code: str) -> None:
    _send_email(email, "Mã khôi phục mật khẩu HVNH Hub", _otp_template(
        title="Khôi phục mật khẩu",
        intro="Bạn vừa yêu cầu đặt lại mật khẩu cho tài khoản HVNH Hub.",
        code=code,
        expiry_minutes=settings.OTP_EXPIRE_MINUTES,
        note="Không chia sẻ mã này với bất kỳ ai, kể cả người tự nhận là nhân viên hỗ trợ.",
    ))


def send_verification_code(email: str, code: str) -> None:
    _send_email(email, "Mã xác thực tài khoản HVNH Hub", _otp_template(
        title="Xác thực tài khoản",
        intro="Hãy nhập mã bên dưới để hoàn tất đăng ký tài khoản bằng email HVNH.",
        code=code,
        expiry_minutes=settings.OTP_EXPIRE_MINUTES,
        note="Chỉ sử dụng mã này trên website HVNH Hub chính thức.",
    ))
