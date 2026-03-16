from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
import random
from .models import User
from .serializers import UserSerializer, UserCreateSerializer, LoginSerializer

User = get_user_model()

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout(request):
    request.auth.delete()
    return Response({'message': 'Successfully logged out'})

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """Register a new user"""
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Generate OTP for email verification
        otp = str(random.randint(100000, 999999))
        request.session['otp'] = otp
        request.session['otp_email'] = user.email
        
        return Response({
            'message': 'User created successfully. Please verify your email.',
            'user': UserSerializer(user).data,
            'otp': otp  # Remove this in production
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp(request):
    """Verify OTP for email verification"""
    email = request.data.get('email')
    otp = request.data.get('otp')
    
    # Verify against stored OTP
    if otp == request.session.get('otp') and email == request.session.get('otp_email'):
        try:
            user = User.objects.get(email=email)
            user.is_active = True
            user.save()
            request.session.pop('otp', None)
            request.session.pop('otp_email', None)
            return Response({'message': 'Email verified successfully'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def forgot_password(request):
    """Send password reset email"""
    email = request.data.get('email')
    
    try:
        user = User.objects.get(email=email)
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Store OTP in session for verification
        otp = str(random.randint(100000, 999999))
        request.session['reset_otp'] = otp
        request.session['reset_email'] = email
        
        return Response({
            'message': 'Password reset instructions sent to your email',
            'uid': uid,
            'token': token,
            'otp': otp  # Remove in production
        })
    except User.DoesNotExist:
        return Response({'error': 'User with this email does not exist'}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    """Reset password with token"""
    uid = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)
        
        if default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password reset successful'})
        else:
            return Response({'error': 'Invalid or expired token'}, 
                           status=status.HTTP_400_BAD_REQUEST)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({'error': 'Invalid reset link'}, 
                       status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password_with_otp(request):
    """Reset password using OTP"""
    email = request.data.get('email')
    otp = request.data.get('otp')
    new_password = request.data.get('new_password')
    
    if otp == request.session.get('reset_otp') and email == request.session.get('reset_email'):
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            request.session.pop('reset_otp', None)
            request.session.pop('reset_email', None)
            return Response({'message': 'Password reset successful'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        return User.objects.filter(id=user.id)

class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        return UserSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        return User.objects.filter(id=user.id)