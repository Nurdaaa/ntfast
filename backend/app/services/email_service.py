import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.email_verification import EmailVerification
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Resend API or SMTP fallback"""

    # Configuration from settings
    SMTP_SERVER = settings.SMTP_SERVER
    SMTP_PORT = settings.SMTP_PORT
    SMTP_USERNAME = settings.SMTP_USERNAME
    SMTP_PASSWORD = settings.SMTP_PASSWORD
    USE_REAL_EMAIL = settings.USE_REAL_EMAIL
    RESEND_API_KEY = settings.RESEND_API_KEY
    EMAIL_PROVIDER = settings.EMAIL_PROVIDER

    # ──────────────────────────────────────────────
    # HTML templates
    # ──────────────────────────────────────────────

    @staticmethod
    def _verification_html(display_name: str, code: str) -> str:
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #ffffff; margin: 0; padding: 0; color: #1d1d1f;">
<div style="max-width: 440px; margin: 0 auto; padding: 60px 24px;">
    <div style="font-size: 26px; font-weight: 600; letter-spacing: -0.022em; margin-bottom: 32px;">Email Verification</div>
    <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">Hi {display_name},</div>
    <div style="font-size: 16px; line-height: 1.5; color: #1d1d1f; margin-bottom: 32px;">
        Enter the verification code below to complete your registration.
    </div>
    <div style="margin-bottom: 40px;">
        <div style="font-size: 42px; font-weight: 700; letter-spacing: 4px; color: #000000;">{code}</div>
        <span style="font-size: 13px; color: #86868b; display: block; margin-top: 8px;">This code expires in 10 minutes.</span>
    </div>
    <div style="font-size: 13px; line-height: 1.5; color: #86868b; border-top: 1px solid #d2d2d7; padding-top: 24px;">
        If you did not request this code, you can safely ignore this email.<br><br>ntFAST
    </div>
</div></body></html>"""

    @staticmethod
    def _password_reset_html(display_name: str, code: str, device: str, location: str, current_time: str) -> str:
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #ffffff; margin: 0; padding: 0; color: #1d1d1f;">
<div style="max-width: 440px; margin: 0 auto; padding: 60px 24px;">
    <div style="font-size: 26px; font-weight: 600; letter-spacing: -0.022em; margin-bottom: 32px;">Password Reset Verification</div>
    <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">Hi {display_name},</div>
    <div style="font-size: 16px; line-height: 1.5; color: #1d1d1f; margin-bottom: 32px;">
        Enter the verification code below to complete the password reset process for your account.
    </div>
    <div style="margin-bottom: 40px;">
        <div style="font-size: 42px; font-weight: 700; letter-spacing: 4px; color: #000000;">{code}</div>
        <span style="font-size: 13px; color: #86868b; display: block; margin-top: 8px;">This code expires in 10 minutes.</span>
    </div>
    <div style="border-top: 1px solid #d2d2d7; padding-top: 24px; margin-bottom: 40px;">
        <div style="font-size: 12px; font-weight: 600; color: #86868b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 16px;">Request Details</div>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="font-size: 14px; color: #86868b; padding: 3px 0; width: 100px;">Device</td><td style="font-size: 14px; font-weight: 500; padding: 3px 0;">{device}</td></tr>
            <tr><td style="font-size: 14px; color: #86868b; padding: 3px 0;">Location</td><td style="font-size: 14px; font-weight: 500; padding: 3px 0;">{location}</td></tr>
            <tr><td style="font-size: 14px; color: #86868b; padding: 3px 0;">Time</td><td style="font-size: 14px; font-weight: 500; padding: 3px 0;">{current_time}</td></tr>
        </table>
    </div>
    <div style="font-size: 13px; line-height: 1.5; color: #86868b; border-top: 1px solid #d2d2d7; padding-top: 24px;">
        If you did not request this code, you can safely ignore this email.<br><br>ntFAST
    </div>
</div></body></html>"""

    # ──────────────────────────────────────────────
    # Sending methods
    # ──────────────────────────────────────────────

    @staticmethod
    def _send_via_resend(to_email: str, subject: str, html_body: str) -> bool:
        """Send email via Resend.com HTTP API — fast & reliable from cloud servers."""
        try:
            response = httpx.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {EmailService.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": "ntFAST <onboarding@resend.dev>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                },
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                logger.info(f"[RESEND] Email sent to {to_email}, id={data.get('id')}")
                return True
            else:
                logger.error(f"[RESEND] Failed to send to {to_email}: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logger.error(f"[RESEND] Exception sending to {to_email}: {e}")
            return False

    @staticmethod
    def _send_via_smtp(to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
        """Send email via SMTP (mail.ru, gmail, etc.)."""
        try:
            message = MIMEMultipart('alternative')
            message['From'] = f"ntFAST <{EmailService.SMTP_USERNAME}>"
            message['To'] = to_email
            message['Subject'] = subject

            if text_body:
                message.attach(MIMEText(text_body, 'plain', 'utf-8'))
            message.attach(MIMEText(html_body, 'html', 'utf-8'))

            if EmailService.SMTP_PORT == 465:
                with smtplib.SMTP_SSL(EmailService.SMTP_SERVER, EmailService.SMTP_PORT) as server:
                    server.login(EmailService.SMTP_USERNAME, EmailService.SMTP_PASSWORD)
                    server.send_message(message)
            else:
                with smtplib.SMTP(EmailService.SMTP_SERVER, EmailService.SMTP_PORT) as server:
                    server.starttls()
                    server.login(EmailService.SMTP_USERNAME, EmailService.SMTP_PASSWORD)
                    server.send_message(message)

            logger.info(f"[SMTP] Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"[SMTP] Failed to send to {to_email}: {e}")
            return False

    @staticmethod
    def _send_email(to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
        """Send email using configured provider (resend or smtp)."""
        # Priority: Resend > SMTP > Demo
        if EmailService.RESEND_API_KEY and EmailService.EMAIL_PROVIDER == "resend":
            return EmailService._send_via_resend(to_email, subject, html_body)
        elif EmailService.USE_REAL_EMAIL and EmailService.SMTP_USERNAME and EmailService.SMTP_PASSWORD:
            return EmailService._send_via_smtp(to_email, subject, html_body, text_body)
        else:
            logger.info(f"[DEMO] Email to {to_email}: subject='{subject}' (no provider configured)")
            return True

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    @staticmethod
    def send_verification_code(email: str, code: str) -> bool:
        """Send verification code to email."""
        display_name = email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
        html_body = EmailService._verification_html(display_name, code)

        result = EmailService._send_email(email, "Email Verification", html_body)

        if not result:
            # Log code for debugging if email fails
            logger.warning(f"[FALLBACK] Verification code for {email}: {code}")

        return result

    @staticmethod
    def send_password_reset_code(email: str, code: str, user_name: str = None,
                                  device_info: str = None, location: str = None,
                                  time_info: str = None) -> bool:
        """Send password reset code to email."""
        display_name = user_name or email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
        device = device_info or "Unknown Device"
        user_location = location or "Unknown Location"

        if time_info:
            current_time = time_info
        else:
            try:
                import pytz
                tz = pytz.timezone('Asia/Almaty')
                now = datetime.now(tz)
                current_time = now.strftime("%B %d, %Y at %H:%M (GMT+5)")
            except (ImportError, KeyError):
                current_time = datetime.now().strftime("%B %d, %Y at %H:%M")

        html_body = EmailService._password_reset_html(display_name, code, device, user_location, current_time)

        result = EmailService._send_email(email, "Password Reset Verification", html_body)

        if not result:
            logger.warning(f"[FALLBACK] Password reset code for {email}: {code}")

        return result

    # ──────────────────────────────────────────────
    # Verification code management (DB)
    # ──────────────────────────────────────────────

    @staticmethod
    def create_verification_code(db: Session, email: str) -> str:
        """Create and store a new verification code"""
        code = EmailVerification.generate_code()

        # Delete old codes for this email
        db.query(EmailVerification).filter(
            EmailVerification.email == email
        ).delete()

        # Create new verification record
        verification = EmailVerification(
            email=email,
            code=code,
            is_verified=False,
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )

        db.add(verification)
        db.commit()

        return code

    @staticmethod
    def verify_code(db: Session, email: str, code: str) -> bool:
        """Verify the code for an email"""
        verification = db.query(EmailVerification).filter(
            EmailVerification.email == email,
            EmailVerification.code == code,
            EmailVerification.is_verified == False,
            EmailVerification.expires_at > datetime.utcnow()
        ).first()

        if not verification:
            return False

        verification.is_verified = True
        db.commit()

        return True
