from django.db.models import Min
from rest_framework import serializers
from ..models import Offer, OfferDetail


class OfferDetailSerializer(serializers.ModelSerializer):
    """Serializer für die vollständige Darstellung und Validierung einer Angebotsstufe."""

    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)

    class Meta:
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
        if value < -1:
            raise serializers.ValidationError('Revisions müssen mindestens -1 sein.')
        return value

    def validate_delivery_time_in_days(self, value):
        if value < 1:
            raise serializers.ValidationError('Lieferzeit muss mindestens 1 Tag betragen.')
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Preis muss größer als 0 sein.')
        return value

    def validate_features(self, value):
        if not isinstance(value, list) or len(value) == 0:
            raise serializers.ValidationError('Mindestens ein Feature muss angegeben werden.')
        return value


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Kurz-Serializer für Angebotsstufen mit ID und Detail-URL."""

    url = serializers.HyperlinkedIdentityField(view_name='offerdetail-detail')

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']


class OfferListSerializer(serializers.ModelSerializer):
    """Serializer für die Angebotsliste inklusive Minimalwerten und Ersteller-Infos."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
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
        if hasattr(obj, 'annotated_min_price') and obj.annotated_min_price is not None:
            return float(obj.annotated_min_price)
        min_val = obj.details.aggregate(min_price=Min('price'))['min_price']
        return float(min_val) if min_val is not None else None

    def get_min_delivery_time(self, obj):
        if hasattr(obj, 'annotated_min_delivery_time') and obj.annotated_min_delivery_time is not None:
            return obj.annotated_min_delivery_time
        return obj.details.aggregate(min_time=Min('delivery_time_in_days'))['min_time']

    def get_user_details(self, obj):
        return {
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'username': obj.user.username,
        }


class OfferRetrieveSerializer(OfferListSerializer):
    """Serializer für die Einzelansicht eines Angebots."""

    class Meta(OfferListSerializer.Meta):
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
    """Serializer zum Erstellen und Aktualisieren eines Angebots samt seiner drei Paketstufen."""

    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = [
            'id',
            'title',
            'image',
            'description',
            'details',
        ]

    def validate_details(self, value):
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
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(**validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)
        instance = super().update(instance, validated_data)
        if details_data is not None:
            self._update_offer_details(instance, details_data)
        return instance

    def _update_offer_details(self, offer, details_data):
        for detail_data in details_data:
            offer_type = detail_data.get('offer_type')
            detail_obj = offer.details.filter(offer_type=offer_type).first()
            if detail_obj:
                for attr, value in detail_data.items():
                    setattr(detail_obj, attr, value)
                detail_obj.save()

