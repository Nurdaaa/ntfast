import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.email_verification import EmailVerification
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""

    # SMTP Configuration from settings
    SMTP_SERVER = settings.SMTP_SERVER
    SMTP_PORT = settings.SMTP_PORT
    SMTP_USERNAME = settings.SMTP_USERNAME
    SMTP_PASSWORD = settings.SMTP_PASSWORD
    USE_REAL_EMAIL = settings.USE_REAL_EMAIL

    @staticmethod
    def send_verification_code(email: str, code: str) -> bool:
        """
        Send verification code to email
        If USE_REAL_EMAIL=true, sends actual email
        Otherwise logs to console (demo mode)
        """
        try:
            if EmailService.USE_REAL_EMAIL and EmailService.SMTP_USERNAME and EmailService.SMTP_PASSWORD:
                # Send real email
                message = MIMEMultipart('alternative')
                message['From'] = f"ntFAST <{EmailService.SMTP_USERNAME}>"
                message['To'] = email
                message['Subject'] = "Email Verification"

                # Get display name from email
                display_name = email.split('@')[0].replace('.', ' ').replace('_', ' ').title()

                # Apple-style minimalist HTML body
                html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
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
            If you did not request this code, you can safely ignore this email. Someone may have entered your email address by mistake.
            <br><br>
            ntFAST
        </div>
    </div>
</body>
</html>
                """

                # Plain text fallback
                text_body = f"""
Email Verification

Hi {display_name},

Enter the verification code below to complete your registration.

Your code: {code}

This code expires in 10 minutes.

If you did not request this code, you can safely ignore this email.

ntFAST
                """

                part1 = MIMEText(text_body, 'plain', 'utf-8')
                part2 = MIMEText(html_body, 'html', 'utf-8')

                message.attach(part1)
                message.attach(part2)

                with smtplib.SMTP(EmailService.SMTP_SERVER, EmailService.SMTP_PORT) as server:
                    server.starttls()
                    server.login(EmailService.SMTP_USERNAME, EmailService.SMTP_PASSWORD)
                    server.send_message(message)

                logger.info(f"Verification email sent to {email}")

            else:
                # Demo mode - log the code so developer can use it
                logger.info(f"[DEMO] Verification code for {email}: {code} (expires in 10 min)")

            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {e}")
            return False

    @staticmethod
    def create_verification_code(db: Session, email: str) -> str:
        """Create and store a new verification code"""
        # Generate code
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

        # Mark as verified
        verification.is_verified = True
        db.commit()

        return True

    @staticmethod
    def send_password_reset_code(email: str, code: str, user_name: str = None, device_info: str = None, location: str = None, time_info: str = None) -> bool:
        """
        Send password reset code to email with Apple-style minimalist design
        If USE_REAL_EMAIL=true, sends actual email
        Otherwise logs to console (demo mode)
        """
        from datetime import datetime
        import pytz

        try:
            # Default values
            display_name = user_name or email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
            device = device_info or "Unknown Device"
            user_location = location or "Unknown Location"

            # Use provided time or generate
            if time_info:
                current_time = time_info
            else:
                try:
                    tz = pytz.timezone('Asia/Almaty')
                    now = datetime.now(tz)
                    current_time = now.strftime("%B %d, %Y at %H:%M (GMT+5)")
                except (ImportError, KeyError):
                    current_time = datetime.now().strftime("%B %d, %Y at %H:%M")

            if EmailService.USE_REAL_EMAIL and EmailService.SMTP_USERNAME and EmailService.SMTP_PASSWORD:
                # Send real email
                message = MIMEMultipart('alternative')
                message['From'] = f"ntFAST <{EmailService.SMTP_USERNAME}>"
                message['To'] = email
                message['Subject'] = "Password Reset Verification"

                # Apple-style minimalist HTML body
                html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
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
                <tr>
                    <td style="font-size: 14px; color: #86868b; padding: 3px 0; width: 100px;">Device</td>
                    <td style="font-size: 14px; font-weight: 500; padding: 3px 0;">{device}</td>
                </tr>
                <tr>
                    <td style="font-size: 14px; color: #86868b; padding: 3px 0;">Location</td>
                    <td style="font-size: 14px; font-weight: 500; padding: 3px 0;">{user_location}</td>
                </tr>
                <tr>
                    <td style="font-size: 14px; color: #86868b; padding: 3px 0;">Time</td>
                    <td style="font-size: 14px; font-weight: 500; padding: 3px 0;">{current_time}</td>
                </tr>
            </table>
        </div>

        <div style="font-size: 13px; line-height: 1.5; color: #86868b; border-top: 1px solid #d2d2d7; padding-top: 24px;">
            If you did not request this code, you can safely ignore this email. Someone may have entered your email address by mistake.
            <br><br>
            ntFAST
        </div>
    </div>
</body>
</html>
                """

                # Plain text fallback
                text_body = f"""
Password Reset Verification

Hi {display_name},

Enter the verification code below to complete the password reset process for your account.

Your code: {code}

This code expires in 10 minutes.

Request Details:
- Device: {device}
- Location: {user_location}
- Time: {current_time}

If you did not request this code, you can safely ignore this email.

ntFAST
                """

                part1 = MIMEText(text_body, 'plain', 'utf-8')
                part2 = MIMEText(html_body, 'html', 'utf-8')

                message.attach(part1)
                message.attach(part2)

                with smtplib.SMTP(EmailService.SMTP_SERVER, EmailService.SMTP_PORT) as server:
                    server.starttls()
                    server.login(EmailService.SMTP_USERNAME, EmailService.SMTP_PASSWORD)
                    server.send_message(message)

                logger.info(f"Password reset email sent to {email}")

            else:
                # Demo mode - log the code so developer can use it
                logger.info(f"[DEMO] Password reset code for {email}: {code} (expires in 10 min)")

            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            return False
