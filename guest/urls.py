from django.urls import path
from .views import GuestTokenView

urlpatterns = [
    path('api/guest-token/', GuestTokenView.as_view(), name='guest-token'),
]
