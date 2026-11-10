from rest_framework import serializers
from ..models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer zum Auflisten und Erstellen von Kundenbewertungen."""

    class Meta:
        model = Review
        fields = [
            'id',
            'business_user',
            'reviewer',
            'rating',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'reviewer', 'created_at', 'updated_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Die Bewertung muss zwischen 1 und 5 Sternen liegen.')
        return value

    def validate_business_user(self, value):
        if not hasattr(value, 'profile') or value.profile.type != 'business':
            raise serializers.ValidationError('Der bewertete Nutzer muss ein Business-Profil besitzen.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        business_user = attrs.get('business_user')
        if request and self.instance is None and business_user:
            already_exists = Review.objects.filter(
                business_user=business_user,
                reviewer=request.user,
            ).exists()
            if already_exists:
                raise serializers.ValidationError(
                    'Du hast für diesen Anbieter bereits eine Bewertung abgegeben.'
                )
        return attrs


class ReviewUpdateSerializer(ReviewSerializer):
    """Serializer zum Aktualisieren von Bewertungstext und Sternen (ohne Wechsel des Business-Nutzers)."""

    class Meta(ReviewSerializer.Meta):
        read_only_fields = ['id', 'business_user', 'reviewer', 'created_at', 'updated_at']

