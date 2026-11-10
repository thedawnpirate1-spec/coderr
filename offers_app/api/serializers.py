"""Serializers for offers and their package tiers."""

from django.db.models import Min
from rest_framework import serializers
from ..models import Offer, OfferDetail


class OfferDetailSerializer(serializers.ModelSerializer):
    """Full representation and validation of a single offer package tier."""

    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)

    class Meta:
        """Serializer options: model and exposed fields."""

        model = OfferDetail
        fields = [
            'id',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
        ]
        extra_kwargs = {
            'offer_type': {'required': False},
        }

    def validate_revisions(self, value):
        """Ensure the number of revisions is at least -1 (-1 means unlimited).

        Args:
            value: The submitted number of revisions.

        Returns:
            The validated value.

        Raises:
            ValidationError: If the value is below -1.
        """
        if value < -1:
            raise serializers.ValidationError('Revisions müssen mindestens -1 sein.')
        return value

    def validate_delivery_time_in_days(self, value):
        """Ensure the delivery time is at least one day.

        Args:
            value: The submitted delivery time in days.

        Returns:
            The validated value.

        Raises:
            ValidationError: If the value is less than 1.
        """
        if value < 1:
            raise serializers.ValidationError('Lieferzeit muss mindestens 1 Tag betragen.')
        return value

    def validate_price(self, value):
        """Ensure the price is greater than zero.

        Args:
            value: The submitted price.

        Returns:
            The validated value.

        Raises:
            ValidationError: If the value is zero or negative.
        """
        if value <= 0:
            raise serializers.ValidationError('Preis muss größer als 0 sein.')
        return value

    def validate_features(self, value):
        """Ensure at least one feature is listed.

        Args:
            value: The submitted list of features.

        Returns:
            The validated value.

        Raises:
            ValidationError: If the value is not a non-empty list.
        """
        if not isinstance(value, list) or len(value) == 0:
            raise serializers.ValidationError('Mindestens ein Feature muss angegeben werden.')
        return value


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Compact representation of a package tier with its ID and detail URL."""

    url = serializers.HyperlinkedIdentityField(view_name='offerdetail-detail')

    class Meta:
        """Serializer options: model and exposed fields."""

        model = OfferDetail
        fields = ['id', 'url']


class OfferListSerializer(serializers.ModelSerializer):
    """Offer representation for lists, including minimum values and creator info."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        """Serializer options: model and exposed fields."""

        model = Offer
        fields = [
            'id',
            'user',
            'title',
            'image',
            'description',
            'created_at',
            'updated_at',
            'details',
            'min_price',
            'min_delivery_time',
            'user_details',
        ]

    def get_min_price(self, obj):
        """Return the cheapest tier price of an offer.

        Uses the queryset annotation when present and falls back to an aggregate query.

        Args:
            obj: The ``Offer`` instance.

        Returns:
            The minimum price as a float, or None if the offer has no tiers.
        """
        annotated = getattr(obj, 'min_price', None)
        if annotated is not None:
            return float(annotated)
        min_val = obj.details.aggregate(val=Min('price'))['val']
        return float(min_val) if min_val is not None else None

    def get_min_delivery_time(self, obj):
        """Return the shortest delivery time of an offer in days.

        Uses the queryset annotation when present and falls back to an aggregate query.

        Args:
            obj: The ``Offer`` instance.

        Returns:
            The minimum delivery time, or None if the offer has no tiers.
        """
        annotated = getattr(obj, 'min_delivery_time', None)
        if annotated is not None:
            return annotated
        return obj.details.aggregate(val=Min('delivery_time_in_days'))['val']

    def get_user_details(self, obj):
        """Return basic public information about the offer's creator.

        Args:
            obj: The ``Offer`` instance.

        Returns:
            A dict with ``first_name``, ``last_name`` and ``username``.
        """
        return {
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'username': obj.user.username,
        }


class OfferRetrieveSerializer(OfferListSerializer):
    """Offer representation for the single-offer view (without creator details)."""

    class Meta(OfferListSerializer.Meta):
        """Serializer options: the list fields minus ``user_details``."""

        fields = [
            'id',
            'user',
            'title',
            'image',
            'description',
            'created_at',
            'updated_at',
            'details',
            'min_price',
            'min_delivery_time',
        ]


class OfferWriteSerializer(serializers.ModelSerializer):
    """Create and update an offer together with its three package tiers."""

    details = OfferDetailSerializer(many=True)

    class Meta:
        """Serializer options: model and exposed fields."""

        model = Offer
        fields = [
            'id',
            'title',
            'image',
            'description',
            'details',
        ]

    def validate_details(self, value):
        """Validate the submitted tiers.

        A new offer must contain exactly the tiers basic, standard and premium.
        When updating, every submitted tier must state its ``offer_type``.

        Args:
            value: The list of validated tier dictionaries.

        Returns:
            The validated list.

        Raises:
            ValidationError: If the tier set is incomplete or an ``offer_type`` is missing.
        """
        if self.instance is None:
            expected_types = {'basic', 'standard', 'premium'}
            provided_types = {item.get('offer_type') for item in value}
            if len(value) != 3 or provided_types != expected_types:
                raise serializers.ValidationError(
                    'Ein neues Angebot muss genau die 3 Stufen basic, standard und premium enthalten.'
                )
        else:
            for item in value:
                if not item.get('offer_type'):
                    raise serializers.ValidationError(
                        'Beim Aktualisieren einer Angebotsstufe muss offer_type angegeben werden.'
                    )
        return value

    def create(self, validated_data):
        """Create an offer and its package tiers.

        Args:
            validated_data: Validated offer fields including the ``details`` list.

        Returns:
            The newly created ``Offer``.
        """
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(**validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer

    def update(self, instance, validated_data):
        """Update an offer and, if provided, the matching package tiers.

        Args:
            instance: The ``Offer`` to update.
            validated_data: Validated offer fields, optionally including ``details``.

        Returns:
            The updated ``Offer``.
        """
        details_data = validated_data.pop('details', None)
        instance = super().update(instance, validated_data)
        if details_data is not None:
            self._update_offer_details(instance, details_data)
        return instance

    def _update_offer_details(self, offer, details_data):
        """Apply partial updates to the tiers of an offer, matched by ``offer_type``.

        Args:
            offer: The ``Offer`` whose tiers are updated.
            details_data: List of tier dictionaries, each containing an ``offer_type``.
        """
        for detail_data in details_data:
            offer_type = detail_data.get('offer_type')
            detail_obj = offer.details.filter(offer_type=offer_type).first()
            if detail_obj:
                for attr, value in detail_data.items():
                    setattr(detail_obj, attr, value)
                detail_obj.save()
