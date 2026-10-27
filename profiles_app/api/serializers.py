from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from ..models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer für die Registrierung von Neukunden und Dienstleistern."""

    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=UserProfile.TYPE_CHOICES, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'type']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('E-Mail-Adresse existiert bereits.')
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('repeated_password'):
            raise serializers.ValidationError({'repeated_password': 'Passwörter stimmen nicht überein.'})
        return attrs

    def create(self, validated_data):
        user_type = validated_data.pop('type')
        validated_data.pop('repeated_password')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user, type=user_type)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer für die Authentifizierung bestehender Benutzer."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('Ungültige Anmeldedaten.')
        attrs['user'] = user
        return attrs
