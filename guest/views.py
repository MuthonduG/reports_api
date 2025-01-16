from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Guest
from django.utils.crypto import get_random_string

class GuestTokenView(APIView):
    def post(self, request):
        # Generate a unique guest identifier
        guest_id = "guest_" + get_random_string(length=16)

        # Create a new Guest entry in the database
        guest = Guest.objects.create(guest_id=guest_id)

        # Generate JWT token with guest_id claim
        access_token = AccessToken()
        access_token['guest_id'] = guest.guest_id

        # Send the token in the response and set as a secure HttpOnly cookie
        response = Response({'access_token': str(access_token)}, status=status.HTTP_201_CREATED)
        response.set_cookie(
            key='jwt',
            value=str(access_token),
            httponly=True,
            secure=True,
            samesite='Strict'
        )
        return response
