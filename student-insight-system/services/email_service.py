"""
Email service — SMTP-based email delivery for password resets.

Uses Python's built-in smtplib so no extra dependencies are needed.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import current_app

logger = logging.getLogger(__name__)


class EmailService:
    """Sends transactional emails via SMTP."""

    @staticmethod
    def _send(to_email: str, subject: str, html_body: str):
        """Low-level SMTP send. Logs errors but never crashes the caller."""
        cfg = current_app.config
        server_addr = cfg.get("MAIL_SERVER")
        port = cfg.get("MAIL_PORT", 587)
        username = cfg.get("MAIL_USERNAME")
        password = cfg.get("MAIL_PASSWORD")
        sender = cfg.get("MAIL_DEFAULT_SENDER") or username

        if not username or not password:
            logger.warning("SMTP credentials not configured — email NOT sent to %s", to_email)
            # Print reset link to console as a fallback during development
            logger.info("Subject: %s | To: %s", subject, to_email)
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Student Insight <{sender}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(server_addr, port, timeout=10) as server:
                server.ehlo()
                if cfg.get("MAIL_USE_TLS", True):
                    server.starttls()
                    server.ehlo()
                server.login(username, password)
                server.sendmail(sender, to_email, msg.as_string())
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s", to_email)
            return False

    @staticmethod
    def send_reset_email(to_email: str, reset_url: str, user_name: str = "User"):
        """Send a styled password-reset email with the magic link."""
        subject = "Reset Your Password — Student Insight"
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin:0; padding:0; background:#f1f5f9; font-family:'Inter',Arial,sans-serif;">
          <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
            <tr><td align="center">
              <table width="480" cellpadding="0" cellspacing="0"
                     style="background:#ffffff; border-radius:16px; overflow:hidden;
                            box-shadow:0 4px 24px rgba(0,45,98,0.08);">
                <!-- Header -->
                <tr>
                  <td style="background:linear-gradient(135deg,#002D62,#001f44);
                             padding:32px 40px; text-align:center;">
                    <span style="color:#D4AF37; font-size:12px; font-weight:700;
                                 letter-spacing:2px; text-transform:uppercase;">
                      Student Insight Platform
                    </span>
                    <h1 style="color:#ffffff; margin:12px 0 0; font-size:24px; font-weight:700;">
                      Password Reset
                    </h1>
                  </td>
                </tr>
                <!-- Body -->
                <tr>
                  <td style="padding:32px 40px;">
                    <p style="color:#1e293b; font-size:15px; line-height:1.6; margin:0 0 20px;">
                      Hi <strong>{user_name}</strong>,
                    </p>
                    <p style="color:#475569; font-size:14px; line-height:1.6; margin:0 0 28px;">
                      We received a request to reset your password. Click the button below
                      to set a new one. This link expires in <strong>5 minutes</strong>.
                    </p>
                    <table width="100%" cellpadding="0" cellspacing="0">
                      <tr><td align="center">
                        <a href="{reset_url}"
                           style="display:inline-block; background:#002D62; color:#ffffff;
                                  padding:14px 36px; border-radius:50px; font-size:14px;
                                  font-weight:600; text-decoration:none;
                                  letter-spacing:0.5px;">
                          Reset My Password
                        </a>
                      </td></tr>
                    </table>
                    <p style="color:#94a3b8; font-size:12px; line-height:1.5; margin:28px 0 0;">
                      If you didn't request this, you can safely ignore this email.
                      Your password won't change until you create a new one.
                    </p>
                  </td>
                </tr>
                <!-- Footer -->
                <tr>
                  <td style="background:#f8fafc; padding:20px 40px; text-align:center;
                             border-top:1px solid #e2e8f0;">
                    <p style="color:#94a3b8; font-size:11px; margin:0;">
                      &copy; Student Insight Platform &bull; Do not reply to this email
                    </p>
                  </td>
                </tr>
              </table>
            </td></tr>
          </table>
        </body>
        </html>
        """
        return EmailService._send(to_email, subject, html)

    @staticmethod
    def send_password_changed_email(to_email: str, user_name: str = "User"):
        """Send a confirmation email after a successful password change."""
        subject = "Password Changed — Student Insight"
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin:0; padding:0; background:#f1f5f9; font-family:'Inter',Arial,sans-serif;">
          <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
            <tr><td align="center">
              <table width="480" cellpadding="0" cellspacing="0"
                     style="background:#ffffff; border-radius:16px; overflow:hidden;
                            box-shadow:0 4px 24px rgba(0,45,98,0.08);">
                <tr>
                  <td style="background:linear-gradient(135deg,#002D62,#001f44);
                             padding:32px 40px; text-align:center;">
                    <span style="color:#D4AF37; font-size:12px; font-weight:700;
                                 letter-spacing:2px; text-transform:uppercase;">
                      Student Insight Platform
                    </span>
                    <h1 style="color:#ffffff; margin:12px 0 0; font-size:24px; font-weight:700;">
                      Password Updated &#10003;
                    </h1>
                  </td>
                </tr>
                <tr>
                  <td style="padding:32px 40px;">
                    <p style="color:#1e293b; font-size:15px; line-height:1.6; margin:0 0 16px;">
                      Hi <strong>{user_name}</strong>,
                    </p>
                    <p style="color:#475569; font-size:14px; line-height:1.6; margin:0 0 20px;">
                      Your password has been successfully changed. You can now sign in
                      with your new password.
                    </p>
                    <p style="color:#ef4444; font-size:13px; line-height:1.5; margin:0;">
                      If you did <strong>not</strong> make this change, please contact
                      support immediately.
                    </p>
                  </td>
                </tr>
                <tr>
                  <td style="background:#f8fafc; padding:20px 40px; text-align:center;
                             border-top:1px solid #e2e8f0;">
                    <p style="color:#94a3b8; font-size:11px; margin:0;">
                      &copy; Student Insight Platform &bull; Do not reply to this email
                    </p>
                  </td>
                </tr>
              </table>
            </td></tr>
          </table>
        </body>
        </html>
        """
        return EmailService._send(to_email, subject, html)
