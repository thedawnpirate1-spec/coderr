"""API views for registration, login and user profiles."""

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
    """Endpoint to register a new user and issue an auth token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Register a new user.

        Args:
            request: The incoming DRF request with the registration data.

        Returns:
            201 with token, username, email and user ID, or 400 with the validation errors.
        """
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
        """Build the response body returned after a successful registration.

        Args:
            user: The newly created user.
            token_key: The user's auth token key.

        Returns:
            A dict with ``token``, ``username``, ``email`` and ``user_id``.
        """
        return {
            'token': token_key,
            'username': user.username,
            'email': user.email,
            'user_id': user.id,
        }


class LoginView(APIView):
    """Endpoint to log in an existing user and return the auth token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Authenticate a user.

        Args:
            request: The incoming DRF request with username and password.

        Returns:
            200 with token, username, email and user ID, or 400 with the validation errors.
        """
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
        """Build the response body returned after a successful login.

        Args:
            user: The authenticated user.
            token_key: The user's auth token key.

        Returns:
            A dict with ``token``, ``username``, ``email`` and ``user_id``.
        """
        return {
            'token': token_key,
            'username': user.username,
            'email': user.email,
            'user_id': user.id,
        }


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Endpoint to retrieve and update a single user profile, looked up by user ID."""

    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'user__pk'
    lookup_url_kwarg = 'pk'


class BusinessProfileListView(generics.ListAPIView):
    """Endpoint listing all business profiles."""

    queryset = UserProfile.objects.select_related('user').filter(type='business')
    serializer_class = BusinessProfileListSerializer
    permission_classes = [IsAuthenticated]


class CustomerProfileListView(generics.ListAPIView):
    """Endpoint listing all customer profiles."""

    queryset = UserProfile.objects.select_related('user').filter(type='customer')
    serializer_class = CustomerProfileListSerializer
    permission_classes = [IsAuthenticated]
