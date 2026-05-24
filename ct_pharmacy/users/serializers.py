# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
from .models import User, OTP
from datetime import datetime, timedelta
import random
from django.contrib.auth.hashers import check_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 
                  'phone', 'address', 'is_active', 'is_email_verified', 
                  'is_phone_verified', 'created_at']
        read_only_fields = ['id', 'created_at', 'is_email_verified', 'is_phone_verified']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 
                  'last_name', 'role', 'phone', 'address']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        
        if attrs.get('phone') and User.objects.filter(phone=attrs['phone']).exists():
            raise serializers.ValidationError({"phone": "Phone number already exists."})
            
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        if not check_password(password, user.password):
            raise serializers.ValidationError("Invalid password")

        if not user.is_active:
            raise serializers.ValidationError("User is inactive")

        return user
class OTPSendSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    otp_type = serializers.ChoiceField(choices=OTP.OTP_TYPE_CHOICES)
    
    def validate(self, data):
        if not data.get('email') and not data.get('phone'):
            raise serializers.ValidationError("Either email or phone is required")
        return data

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    otp = serializers.CharField(max_length=6)
    otp_type = serializers.ChoiceField(choices=OTP.OTP_TYPE_CHOICES)
    
    def validate(self, data):
        if not data.get('email') and not data.get('phone'):
            raise serializers.ValidationError("Either email or phone is required")
        return data

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords don't match"})
        return data