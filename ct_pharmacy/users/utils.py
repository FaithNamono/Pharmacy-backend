# utils.py
import requests
from django.conf import settings
import random
import string

def send_email_otp(email, otp_code, otp_type='verification'):
    """
    Send OTP via email using Brevo's transactional email API (HTTPS).

    We switched away from Django's SMTP backend because raw SMTP (port 587)
    appears to be blocked or heavily throttled on Render's free tier — it
    was hanging long enough to trigger Gunicorn WORKER TIMEOUT crashes with
    no error ever surfacing. Brevo's API is a plain HTTPS POST (port 443),
    which free-tier hosts don't block, and it fails fast with a clear error
    instead of hanging indefinitely.
    """
    if otp_type == 'verification':
        subject = 'Verify Your Email - Dervin Pharmacy'
        heading = 'Verify Your Email'
        body_text = 'Your verification code for Dervin Pharmacy is:'
    else:  # password reset
        subject = 'Password Reset OTP - Dervin Pharmacy'
        heading = 'Password Reset Request'
        body_text = 'Your password reset OTP is:'

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>{heading}</h2>
        <p>Hello,</p>
        <p>{body_text}</p>
        <p style="font-size: 28px; font-weight: bold; letter-spacing: 4px;
                   background: #f2f2f2; padding: 12px 20px; display: inline-block;
                   border-radius: 6px;">{otp_code}</p>
        <p>This code will expire in 10 minutes.</p>
        <p>If you didn't request this, please ignore this email.</p>
        <p>Best regards,<br>Dervin Pharmacy Team</p>
      </body>
    </html>
    """

    payload = {
        "sender": {
            "name": settings.BREVO_SENDER_NAME,
            "email": settings.BREVO_SENDER_EMAIL,
        },
        "to": [{"email": email}],
        "subject": subject,
        "htmlContent": html_content,
    }

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers=headers,
            timeout=10,  # fail fast rather than hang — this is the whole point
        )

        if response.status_code in (200, 201):
            return True

        print(f"Brevo email failed: status={response.status_code} body={response.text}")
        return False

    except requests.exceptions.Timeout:
        print(f"Brevo email timed out after 10s for {email}")
        return False
    except Exception as e:
        print(f"Brevo email sending failed: {e}")
        return False


def send_sms_otp(phone_number, otp_code, otp_type='verification'):
    """
    SMS OTP is currently unsupported — no SMS provider is configured, and
    the app no longer exposes a phone-verification option in its UI.
    This is kept as a stub so send_otp() in views.py doesn't break if it's
    ever called; it always reports failure.
    """
    print(f"SMS OTP requested for {phone_number} but no SMS provider is configured.")
    return False


def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))