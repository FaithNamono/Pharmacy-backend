# ct_pharmacy/users/views.py

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from .models import User, OTP
from .serializers import (
    UserCreateSerializer, LoginSerializer, OTPSendSerializer,
    OTPVerifySerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
    UserSerializer
)
from .utils import send_email_otp, send_sms_otp, generate_otp

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def register(request):
    """Register new user and send verification OTP"""
    print("Register endpoint hit")
    print("Request data:", request.data)

    serializer = UserCreateSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        # Send email verification OTP
        otp_code = generate_otp()
        OTP.objects.create(
            user=user,
            otp_code=otp_code,
            otp_type='email',
            destination=user.email,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # Attempt to send the email and actually check whether it succeeded.
        # send_email_otp() catches its own exceptions and returns True/False —
        # it never raises — so this must check the return value, not rely on
        # a try/except here (that would never trigger).
        email_sent = False
        try:
            email_sent = send_email_otp(user.email, otp_code, 'verification')
        except Exception as e:
            print(f"Email sending error: {e}")

        response_data = {
            'success': True,
            'message': 'Registration successful. Please verify your email.',
            'user': UserSerializer(user).data
        }

        if not email_sent:
            print(f"WARNING: verification email failed to send to {user.email}")
            response_data['email_warning'] = (
                'Account created, but the verification email could not be sent. '
                'Please use "Resend OTP" on the verification screen, or contact support.'
            )
            # Also include the OTP directly as a fallback while email delivery
            # is unreliable on the free tier — remove this once email is confirmed working.
            response_data['test_otp'] = otp_code

        return Response(response_data, status=status.HTTP_201_CREATED)

    print("Validation errors:", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def login_view(request):
    """Login user"""
    print("Login endpoint hit")
    print("Request data:", request.data)

    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.validated_data
        login(request, user)

        # Check if email is verified
        if not user.is_email_verified:
            return Response({
                'success': False,
                'error': 'Please verify your email before logging in.',
                'requires_verification': True,
                'email': user.email
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Add token generation
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'success': True,
            'message': 'Login successful',
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

    print("Login validation errors:", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def send_otp(request):
    """Send OTP for verification or password reset"""
    print("Send OTP endpoint hit")
    print("Request data:", request.data)

    serializer = OTPSendSerializer(data=request.data)

    if serializer.is_valid():
        otp_type = serializer.validated_data['otp_type']
        email = serializer.validated_data.get('email')
        phone = serializer.validated_data.get('phone')

        # Find user
        user = None
        destination = email or phone

        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'error': 'No user found with this email'
                }, status=status.HTTP_404_NOT_FOUND)
        elif phone:
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                return Response({
                    'error': 'No user found with this phone number'
                }, status=status.HTTP_404_NOT_FOUND)

        # Generate and save OTP
        otp_code = generate_otp()
        OTP.objects.create(
            user=user,
            otp_code=otp_code,
            otp_type=otp_type,
            destination=destination,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # Send OTP
        sent = False
        if email:
            sent = send_email_otp(email, otp_code, otp_type)
        elif phone:
            sent = send_sms_otp(phone, otp_code, otp_type)

        if sent:
            return Response({
                'success': True,
                'message': f'OTP sent successfully to {destination}'
            }, status=status.HTTP_200_OK)
        else:
            # For development, return success anyway with the OTP
            return Response({
                'success': True,
                'message': f'Test OTP for {destination} is: {otp_code} (Email sending may not be configured)',
                'test_otp': otp_code
            }, status=status.HTTP_200_OK)

    print("Send OTP validation errors:", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify OTP"""
    print("Verify OTP endpoint hit")
    print("Request data:", request.data)

    serializer = OTPVerifySerializer(data=request.data)

    if serializer.is_valid():
        otp_code = serializer.validated_data['otp']
        otp_type = serializer.validated_data['otp_type']
        email = serializer.validated_data.get('email')
        phone = serializer.validated_data.get('phone')

        # Find user
        user = None
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
        elif phone:
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)

        # Find valid OTP
        try:
            otp = OTP.objects.get(
                user=user,
                otp_code=otp_code,
                otp_type=otp_type,
                is_used=False
            )

            if otp.is_valid():
                otp.is_used = True
                otp.save()

                # Update user verification status
                if otp_type == 'email':
                    user.is_email_verified = True
                    user.save()
                elif otp_type == 'phone':
                    user.is_phone_verified = True
                    user.save()

                return Response({
                    'success': True,
                    'message': 'OTP verified successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'OTP has expired'
                }, status=status.HTTP_400_BAD_REQUEST)

        except OTP.DoesNotExist:
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)

    print("Verify OTP validation errors:", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def forgot_password(request):
    """Send OTP for password reset"""
    print("Forgot password endpoint hit")
    print("Request data:", request.data)

    serializer = ForgotPasswordSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)

            # Send password reset OTP
            otp_code = generate_otp()
            OTP.objects.create(
                user=user,
                otp_code=otp_code,
                otp_type='reset',
                destination=email,
                expires_at=timezone.now() + timedelta(minutes=10)
            )

            email_sent = False
            try:
                email_sent = send_email_otp(email, otp_code, 'reset')
            except Exception as e:
                print(f"Email sending error: {e}")

            response_data = {
                'success': True,
                'message': 'If an account exists, a password reset code has been sent.'
            }

            if not email_sent:
                print(f"WARNING: reset email failed to send to {email}")
                response_data['message'] = (
                    'Account found, but the reset email could not be sent. '
                    'Please try again shortly or contact support.'
                )
                # Fallback while email delivery is unreliable on the free tier —
                # remove this once email is confirmed working.
                response_data['test_otp'] = otp_code

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            return Response({
                'success': True,
                'message': 'If an account exists, you will receive reset instructions'
            }, status=status.HTTP_200_OK)

    print("Forgot password validation errors:", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password using OTP"""
    print("Reset password endpoint hit")
    print("Request data:", request.data)

    serializer = ResetPasswordSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)

            # Verify OTP
            try:
                otp = OTP.objects.get(
                    user=user,
                    otp_code=otp_code,
                    otp_type='reset',
                    is_used=False
                )

                if otp.is_valid():
                    otp.is_used = True
                    otp.save()

                    # Reset password
                    user.set_password(new_password)
                    user.save()

                    return Response({
                        'success': True,
                        'message': 'Password reset successfully'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'OTP has expired'
                    }, status=status.HTTP_400_BAD_REQUEST)

            except OTP.DoesNotExist:
                return Response({
                    'error': 'Invalid OTP'
                }, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

    print("Reset password validation errors:", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ============================================================
# CHANGE PASSWORD ENDPOINT
# ============================================================

@api_view(['POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password for authenticated user (when they know current password)"""
    print("Change password endpoint hit")
    print("Request data:", request.data)

    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    # Validate inputs
    if not current_password or not new_password:
        return Response({
            'success': False,
            'error': 'Current password and new password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check if current password is correct
    if not user.check_password(current_password):
        return Response({
            'success': False,
            'error': 'Current password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check if passwords match
    if new_password != confirm_password:
        return Response({
            'success': False,
            'error': 'New passwords do not match'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Validate password strength
    if len(new_password) < 6:
        return Response({
            'success': False,
            'error': 'Password must be at least 6 characters'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Change password
    user.set_password(new_password)
    user.save()

    return Response({
        'success': True,
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)

# ============================================================
# GET CURRENT USER ENDPOINT
# ============================================================

@api_view(['GET'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get current logged in user"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

# ============================================================
# LOGOUT ENDPOINT
# ============================================================

@api_view(['POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout user"""
    # Delete the auth token
    try:
        request.user.auth_token.delete()
    except Exception:
        pass

    return Response({'success': True, 'message': 'Logged out successfully'})

# ============================================================
# USER MANAGEMENT ENDPOINTS (Admin Only)
# ============================================================

@api_view(['GET', 'POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def users_list_create(request):
    """GET: list all users, POST: create a user - Admin only"""
    if request.user.role != 'admin':
        return Response({
            'error': 'You do not have permission to manage users'
        }, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        users = User.objects.all().order_by('-date_joined')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    # POST
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # This user is being created directly by an admin (not through public
        # self-registration), so the admin is already vouching for this person
        # and their email. Skip the OTP-based email verification step entirely —
        # relying on it here would leave the new staff member permanently unable
        # to log in if email delivery fails (which the register() flow has shown
        # to be unreliable on Render's free tier). Auto-mark them verified so
        # they can log in immediately with the password the admin set.
        user.is_email_verified = True
        user.save()

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'PATCH', 'DELETE'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def user_detail(request, user_id):
    """PUT/PATCH: update a user, DELETE: remove a user - Admin only"""
    if request.user.role != 'admin':
        return Response({
            'error': 'You do not have permission to manage users'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        if user.id == request.user.id:
            return Response({
                'error': 'You cannot delete your own account'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        return Response({
            'message': 'User deleted successfully'
        }, status=status.HTTP_200_OK)

    # PUT / PATCH
    data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
    data.pop('is_superuser', None)

    serializer = UserSerializer(user, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)