# utils.py
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
import random
import string

def send_email_otp(email, otp_code, otp_type='verification'):
    """Send OTP via email"""
    if otp_type == 'verification':
        subject = 'Verify Your Email - Dervin Pharmacy'
        message = f'''
        Hello,
        
        Your verification code for Dervin Pharmacy is: {otp_code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Dervin Pharmacy Team
        '''
    else:  # password reset
        subject = 'Password Reset OTP - Dervin Pharmacy'
        message = f'''
        Hello,
        
        Your password reset OTP is: {otp_code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Dervin Pharmacy Team
        '''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def send_sms_otp(phone_number, otp_code, otp_type='verification'):
    """Send OTP via SMS using Twilio"""
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        if otp_type == 'verification':
            message_body = f'Your Dervin Pharmacy verification code is: {otp_code}'
        else:
            message_body = f'Your Dervin Pharmacy password reset code is: {otp_code}'
        
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return True
    except Exception as e:
        print(f"SMS sending failed: {e}")
        return False

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))