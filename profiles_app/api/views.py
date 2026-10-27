from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
)


class RegistrationView(APIView):
    """Endpunkt zur Registrierung eines neuen Benutzers mit automatischer Token-Erstellung."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            self._build_auth_response(user, token.key),
            status=status.HTTP_201_CREATED,
        )

    def _build_auth_response(self, user, token_key):
        return {
            'token': token_key,
            'username': user.username,
            'email': user.email,
            'user_id': user.id,
        }


class LoginView(APIView):
    """Endpunkt zur Anmeldung eines bestehenden Nutzers mit Token-Rückgabe."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            self._build_auth_response(user, token.key),
            status=status.HTTP_200_OK,
        )

    def _build_auth_response(self, user, token_key):
        return {
            'token': token_key,
            'username': user.username,
            'email': user.email,
            'user_id': user.id,
        }
