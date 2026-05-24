# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random
import string

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('customer', 'Customer'),
    )
    
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.username

class OTP(models.Model):
    OTP_TYPE_CHOICES = (
        ('email', 'Email Verification'),
        ('phone', 'Phone Verification'),
        ('reset', 'Password Reset'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=10, choices=OTP_TYPE_CHOICES)
    destination = models.CharField(max_length=100)  # email or phone number
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()
    
    @staticmethod
    def generate_otp():
        return ''.join(random.choices(string.digits, k=6))
    
    def __str__(self):
        return f"{self.user.username} - {self.otp_code}"