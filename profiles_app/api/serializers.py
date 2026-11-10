"""Serializers for registration, login and user profiles."""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from ..models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate and create a new customer or business user together with a profile."""

    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=UserProfile.TYPE_CHOICES, write_only=True)

    class Meta:
        """Serializer options: model, exposed fields and extra field arguments."""

        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'type']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def validate_email(self, value):
        """Ensure the email address is not registered yet.

        Args:
            value: The submitted email address.

        Returns:
            The validated email address.

        Raises:
            ValidationError: If a user with this email already exists.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('E-Mail-Adresse existiert bereits.')
        return value

    def validate(self, attrs):
        """Ensure the password and its repetition match.

        Args:
            attrs: The validated attributes.

        Returns:
            The unchanged attributes.

        Raises:
            ValidationError: If ``password`` and ``repeated_password`` differ.
        """
        if attrs.get('password') != attrs.get('repeated_password'):
            raise serializers.ValidationError({'repeated_password': 'Passwörter stimmen nicht überein.'})
        return attrs

    def create(self, validated_data):
        """Create the user (with a hashed password) and the matching profile.

        Args:
            validated_data: Validated registration data.

        Returns:
            The newly created ``User``.
        """
        user_type = validated_data.pop('type')
        validated_data.pop('repeated_password')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user, type=user_type)
        return user


class LoginSerializer(serializers.Serializer):
    """Authenticate an existing user by username and password."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Check the credentials and attach the authenticated user.

        Args:
            attrs: The submitted username and password.

        Returns:
            The attributes extended by the authenticated ``user``.

        Raises:
            ValidationError: If the credentials are invalid.
        """
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('Ungültige Anmeldedaten.')
        attrs['user'] = user
        return attrs


class ProfileDetailSerializer(serializers.ModelSerializer):
    """Retrieve and update a single profile, flattened together with its user fields."""

    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        """Serializer options: model, exposed fields and read-only fields."""

        model = UserProfile
        fields = [
            'user',
            'username',
            'first_name',
            'last_name',
            'file',
            'location',
            'tel',
            'description',
            'working_hours',
            'type',
            'email',
            'created_at',
        ]
        read_only_fields = ['user', 'username', 'type', 'created_at']

    def update(self, instance, validated_data):
        """Update the profile and the related user fields in one request.

        Args:
            instance: The ``UserProfile`` to update.
            validated_data: Validated data, with user fields nested under ``user``.

        Returns:
            The updated ``UserProfile``.
        """
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        if user_data:
            instance.user.save()
        return super().update(instance, validated_data)


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """List representation of business profiles."""

    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        """Serializer options: model and exposed fields."""

        model = UserProfile
        fields = [
            'user',
            'username',
            'first_name',
            'last_name',
            'file',
            'location',
            'tel',
            'description',
            'working_hours',
            'type',
        ]


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """List representation of customer profiles."""

    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    uploaded_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        """Serializer options: model and exposed fields."""

        model = UserProfile
        fields = [
            'user',
            'username',
            'first_name',
            'last_name',
            'file',
            'uploaded_at',
            'type',
        ]
