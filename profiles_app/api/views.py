from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from ..models import UserProfile
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
    ProfileDetailSerializer,
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
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


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Endpunkt zum Abrufen und Bearbeiten eines einzelnen Benutzerprofils anhand der User-ID."""

    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'user__pk'
    lookup_url_kwarg = 'pk'


class BusinessProfileListView(generics.ListAPIView):
    """Endpunkt zum Auflisten aller Geschäftsprofile."""

    queryset = UserProfile.objects.select_related('user').filter(type='business')
    serializer_class = BusinessProfileListSerializer
    permission_classes = [IsAuthenticated]


class CustomerProfileListView(generics.ListAPIView):
    """Endpunkt zum Auflisten aller Kundenprofile."""

    queryset = UserProfile.objects.select_related('user').filter(type='customer')
    serializer_class = CustomerProfileListSerializer
    permission_classes = [IsAuthenticated]
