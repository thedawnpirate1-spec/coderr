"""Serializers for creating, listing and updating customer reviews."""

from rest_framework import serializers
from ..models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """List and create customer reviews with rating and duplicate validation."""

    class Meta:
        """Serializer options: model, exposed fields and read-only fields."""

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
        """Ensure the rating is between 1 and 5 stars.

        Args:
            value: The submitted rating.

        Returns:
            The validated rating.

        Raises:
            ValidationError: If the rating is outside the range 1 to 5.
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError('Die Bewertung muss zwischen 1 und 5 Sternen liegen.')
        return value

    def validate_business_user(self, value):
        """Ensure the reviewed user has a business profile.

        Args:
            value: The submitted business user.

        Returns:
            The validated user.

        Raises:
            ValidationError: If the user has no business profile.
        """
        if not hasattr(value, 'profile') or value.profile.type != 'business':
            raise serializers.ValidationError('Der bewertete Nutzer muss ein Business-Profil besitzen.')
        return value

    def validate(self, attrs):
        """Ensure a reviewer cannot review the same business user twice.

        Args:
            attrs: The validated attributes.

        Returns:
            The unchanged attributes.

        Raises:
            ValidationError: If the requesting user already reviewed this business user.
        """
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
    """Update a review's text and rating without changing the reviewed business user."""

    class Meta(ReviewSerializer.Meta):
        """Serializer options: additionally marks ``business_user`` as read-only."""

        read_only_fields = ['id', 'business_user', 'reviewer', 'created_at', 'updated_at']
