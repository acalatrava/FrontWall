import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings

logger = logging.getLogger("frontwall.services.email")


def _is_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from_email)


def _send_raw(to: str, subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if settings.smtp_use_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
            server.ehlo()
            server.starttls()
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
            server.ehlo()

        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)

        server.sendmail(settings.smtp_from_email, [to], msg.as_string())
        server.quit()
        logger.info("Email sent to %s: %s", to, subject)
    except Exception:
        logger.exception("Failed to send email to %s", to)
        raise


async def send_email(to: str, subject: str, html_body: str) -> None:
    if not _is_configured():
        logger.warning("SMTP not configured — email to %s not sent", to)
        return
    await asyncio.to_thread(_send_raw, to, subject, html_body)


def _base_template(title: str, content: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:520px;margin:40px auto;background:#111118;border:1px solid #1e1e2e;border-radius:16px;overflow:hidden;">
  <div style="padding:28px 32px;border-bottom:1px solid #1e1e2e;text-align:center;">
    <span style="font-size:20px;font-weight:700;color:#fff;">&#128737;&#65039; FrontWall</span>
  </div>
  <div style="padding:32px;">
    <h2 style="color:#fff;margin:0 0 16px;font-size:20px;">{title}</h2>
    {content}
  </div>
  <div style="padding:16px 32px;border-top:1px solid #1e1e2e;text-align:center;">
    <p style="color:#555;font-size:11px;margin:0;">This email was sent by FrontWall. Do not reply.</p>
  </div>
</div>
</body>
</html>"""


async def send_invite(to: str, invite_url: str, inviter: str) -> None:
    content = f"""
    <p style="color:#9ca3af;font-size:14px;line-height:1.6;">
      <strong style="color:#fff;">{inviter}</strong> has invited you to join the FrontWall security dashboard.
    </p>
    <p style="color:#9ca3af;font-size:14px;line-height:1.6;">
      Click the button below to set up your account. This link expires in <strong style="color:#fff;">48 hours</strong>.
    </p>
    <div style="text-align:center;margin:28px 0;">
      <a href="{invite_url}" style="display:inline-block;padding:12px 32px;background:#2563eb;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;font-size:14px;">Accept Invitation</a>
    </div>
    <p style="color:#6b7280;font-size:11px;">If you didn't expect this, ignore it.</p>"""
    await send_email(to, "You're invited to FrontWall", _base_template("You're Invited", content))


async def send_password_reset(to: str, reset_url: str) -> None:
    content = f"""
    <p style="color:#9ca3af;font-size:14px;line-height:1.6;">
      A password reset was requested for your FrontWall account.
    </p>
    <p style="color:#9ca3af;font-size:14px;line-height:1.6;">
      Click the button below to set a new password. This link expires in <strong style="color:#fff;">1 hour</strong>.
    </p>
    <div style="text-align:center;margin:28px 0;">
      <a href="{reset_url}" style="display:inline-block;padding:12px 32px;background:#2563eb;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;font-size:14px;">Reset Password</a>
    </div>
    <p style="color:#6b7280;font-size:11px;">If you didn't request this, your account is safe — ignore this email.</p>"""
    await send_email(to, "FrontWall Password Reset", _base_template("Reset Your Password", content))
