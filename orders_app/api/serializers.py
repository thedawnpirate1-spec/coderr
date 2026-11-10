"""Serializers for reading, creating and updating orders."""

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from offers_app.models import OfferDetail
from ..models import Order


class OrderSerializer(serializers.ModelSerializer):
    """Read-only representation of an order."""

    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)

    class Meta:
        """Serializer options: model and exposed fields (all read-only)."""

        model = Order
        fields = [
            'id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class OrderCreateSerializer(serializers.ModelSerializer):
    """Create an order from an ``offer_detail_id`` by snapshotting the offer tier."""

    offer_detail_id = serializers.IntegerField(write_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)

    class Meta:
        """Serializer options: model, exposed fields and read-only fields."""

        model = Order
        fields = [
            'id',
            'offer_detail_id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'status',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data):
        """Create an order by copying the data of the referenced offer tier.

        Args:
            validated_data: Validated input containing ``offer_detail_id``.

        Returns:
            The newly created ``Order`` with status ``in_progress``.

        Raises:
            Http404: If no offer tier with the given ID exists.
        """
        offer_detail_id = validated_data['offer_detail_id']
        offer_detail = get_object_or_404(
            OfferDetail.objects.select_related('offer__user'),
            pk=offer_detail_id,
        )
        return Order.objects.create(
            customer_user=self.context['request'].user,
            business_user=offer_detail.offer.user,
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
            status='in_progress',
        )


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Update the status of an order; all other fields are read-only."""

    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES, required=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)

    class Meta:
        """Serializer options: model, exposed fields and read-only fields."""

        model = Order
        fields = [
            'id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        """Reject requests that try to modify anything other than ``status``.

        Args:
            attrs: The validated attributes.

        Returns:
            The unchanged attributes.

        Raises:
            ValidationError: If the request body contains fields besides ``status``.
        """
        unknown_fields = set(self.initial_data.keys()) - {'status'}
        if unknown_fields:
            raise serializers.ValidationError({'status': 'Nur das Feld status darf aktualisiert werden.'})
        return attrs
