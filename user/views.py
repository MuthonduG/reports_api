from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from .models import User, OtpToken
from .serializers import UserSerializer 
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail
from .signals import create_token
import logging
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


logger = logging.getLogger(__name__)

# Custom JWT token serializer
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        token['anonymous_unique_id'] = user.anonymous_unique_id

        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# get all users
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUsers(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

# get single user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUser(request, pk):
    user = get_object_or_404(User, id=pk)
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)

# sign up new user (only admin user can regiser a new user)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])  
def registerUser(request):
    if not request.user.is_staff:
        return Response(
            {"message": "You do not have permission to perform this action."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Generate JWT token after successful registration
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        return Response({
            "user": serializer.data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    else:
        logger.error(f"Registration errors: {serializer.errors}")
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


# update user data
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateUser(request, pk):
    user = get_object_or_404(User, id=pk)
    serializer = UserSerializer(instance=user, data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

# delete user
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteUser(request, pk):
    user = get_object_or_404(User, id=pk)
    user.delete()
    return Response(
        {"message": "User account successfully deleted!"},
        status=status.HTTP_204_NO_CONTENT
    )

# activate account using OTP
@api_view(['POST'])
@permission_classes([AllowAny]) 
def verifyEmail(request):
    # Extract email and OTP from request data
    email = request.data.get("email")
    otp_code = request.data.get("otp_code")
    
    if not email or not otp_code:
        return Response(
            {"message": "Email and OTP code are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Fetch the user by email
    user = get_object_or_404(User, email=email)

    # Fetch the most recent OTP for the user
    user_otp = OtpToken.objects.filter(user=user).last()

    if not user_otp:
        return Response(
            {"message": "No OTP found for this user."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Check if OTP has expired
    if timezone.now() > user_otp.otp_expires_at:
        return Response(
            {"message": "The OTP has expired. Please request a new one."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate the provided OTP code (case insensitive)
    if user_otp.otp_code.lower() != otp_code.lower():
        return Response(
            {"message": "Invalid OTP. Please try again."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Activate the user's account
    user.is_active = True
    user.is_staff = True
    user.save()
    logger.info(f"User {user.email} activated their account using OTP.")

    # Send confirmation email
    try:
        send_mail(
            subject="Account Activated",
            message="Your account has been successfully activated!",
            from_email="muthondugithinji@gmail.com",  
            recipient_list=[user.email],
            fail_silently=False, 
        )
    except Exception as e:
        logger.error(f"Failed to send activation email to {user.email}: {e}")

    # Invalidate the OTP
    user_otp.delete()

    return Response(
        {"message": "Account has been activated successfully!"},
        status=status.HTTP_200_OK,
    )

# resend OTP
@api_view(['POST'])
def resendOtp(request, email):
    user = get_object_or_404(User, email=email)
    OtpToken.objects.filter(user=user, otp_expires_at=timezone.now()).delete()

    try:
        create_token(user)
        logger.info(f"Generated and sent new OTP for user {user.email}")
    except Exception as e:
        logger.error(f"Failed to generate/send OTP for {user.email}: {e}")
        return Response(
            {"message": "Failed to send OTP. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {"message": "A new OTP has been sent to your email address."},
        status=status.HTTP_200_OK,
    )