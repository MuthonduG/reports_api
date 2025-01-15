from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView, getUsers, registerUser, getUser, updateUser, deleteUser, verifyEmail, resendOtp

urlpatterns = [
    path('get_users', getUsers),
    path('register', registerUser),
    path('login', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'), 
    path('get_user/<str:pk>', getUser),
    path('update_user/<str:pk>', updateUser),
    path('delete_user/<str:pk>', deleteUser),
    path('verify_email', verifyEmail),
    path('resend_otp', resendOtp)
]