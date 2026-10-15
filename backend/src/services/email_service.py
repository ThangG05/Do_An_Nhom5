import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote

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


def send_password_reset_code(email: str, code: str, *, account_email: str | None = None) -> None:
    account_note = f" cho tài khoản {account_email}" if account_email else ""
    _send_email(email, "Mã khôi phục mật khẩu HVNH Hub", _otp_template(
        title="Khôi phục mật khẩu",
        intro=f"Bạn vừa yêu cầu đặt lại mật khẩu{account_note} trên HVNH Hub.",
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


def _feedback_template(*, sender_email: str, sender_name: str, message: str) -> str:
    safe_name = html.escape(sender_name.strip() or "Sinh viên HVNH")
    safe_email = html.escape(sender_email.strip())
    mailto_email = html.escape(quote(sender_email.strip(), safe="@._+-"), quote=True)
    safe_message = html.escape(message.strip()).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")

    return f"""<!doctype html>
<html lang="vi">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Góp ý từ sinh viên HVNH Hub</title>
  </head>
  <body style="margin:0;padding:0;background-color:#f3f6fb;color:#17365d;font-family:Arial,Helvetica,sans-serif;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;background-color:#f3f6fb;">
      <tr><td align="center" style="padding:32px 12px;">
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%;max-width:620px;border-collapse:separate;background-color:#ffffff;border:1px solid #dce5f0;border-radius:18px;overflow:hidden;">
          <tr><td style="padding:28px 32px 30px;background-color:#0b3158;color:#ffffff;">
            <div style="font-size:12px;font-weight:700;letter-spacing:2px;color:#f7c948;">HVNH HUB</div>
            <h1 style="margin:14px 0 8px;font-size:25px;line-height:1.25;font-weight:700;color:#ffffff;">Có góp ý mới từ sinh viên</h1>
            <p style="margin:0;font-size:14px;line-height:1.6;color:#d9e8f7;">Phản hồi được gửi từ biểu mẫu Liên hệ và Góp ý.</p>
          </td></tr>
          <tr><td style="padding:30px 32px 28px;">
            <p style="margin:0 0 12px;font-size:12px;font-weight:700;letter-spacing:1.4px;color:#607792;">THÔNG TIN NGƯỜI GỬI</p>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;background-color:#f6f9fd;border:1px solid #e2eaf3;border-radius:12px;">
              <tr><td style="padding:18px 20px;">
                <div style="font-size:17px;line-height:1.45;font-weight:700;color:#102f52;overflow-wrap:anywhere;word-break:break-word;">{safe_name}</div>
                <div style="margin-top:5px;font-size:14px;line-height:1.5;overflow-wrap:anywhere;word-break:break-word;"><a href="mailto:{mailto_email}" style="color:#1765a5;text-decoration:none;">{safe_email}</a></div>
              </td></tr>
            </table>
            <p style="margin:27px 0 12px;font-size:12px;font-weight:700;letter-spacing:1.4px;color:#607792;">NỘI DUNG GÓP Ý</p>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;background-color:#fffaf0;border-left:4px solid #f4bd37;border-radius:0 12px 12px 0;">
              <tr><td style="padding:20px 22px;font-size:16px;line-height:1.7;color:#233b55;overflow-wrap:anywhere;word-break:break-word;">{safe_message}</td></tr>
            </table>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:separate;margin-top:28px;">
              <tr><td style="background-color:#0b3158;border-radius:10px;">
                <a href="mailto:{mailto_email}" style="display:inline-block;padding:13px 21px;color:#ffffff;font-size:14px;font-weight:700;text-decoration:none;">Trả lời góp ý</a>
              </td></tr>
            </table>
          </td></tr>
          <tr><td style="padding:18px 32px;border-top:1px solid #e7edf5;background-color:#fbfcfe;color:#71849a;font-size:12px;line-height:1.6;">
            Email này được gửi tự động từ HVNH Hub. Để phản hồi, hãy dùng nút “Trả lời góp ý” hoặc liên hệ địa chỉ người gửi ở trên.
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>"""


def send_user_feedback(*, sender_email: str, sender_name: str, message: str) -> None:
    recipient = settings.FEEDBACK_TO_EMAIL or settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    if not recipient:
        raise EmailDeliveryError("Email nhận góp ý chưa được cấu hình.")
    _send_email(recipient, "Góp ý từ sinh viên HVNH Hub", _feedback_template(
        sender_email=sender_email,
        sender_name=sender_name,
        message=message,
    ))
