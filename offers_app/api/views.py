from decimal import Decimal, InvalidOperation
from django.db.models import Min
from rest_framework import filters, generics
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from ..models import Offer, OfferDetail
from .permissions import IsBusinessUserOrReadOnly, IsOfferOwnerOrReadOnly
from .serializers import (
    OfferDetailSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
    OfferWriteSerializer,
)


class OfferPagination(PageNumberPagination):
    """Seitennummerierung für die Angebotsliste mit standardmäßig 6 Einträgen pro Seite."""

    page_size = 6
    page_size_query_param = 'page_size'


class OfferListCreateView(generics.ListCreateAPIView):
    """Endpunkt zum Auflisten, Filtern und Erstellen von Angeboten."""

    permission_classes = [IsBusinessUserOrReadOnly]
    pagination_class = OfferPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OfferWriteSerializer
        return OfferListSerializer

    def get_queryset(self):
        queryset = (
            Offer.objects.select_related('user')
            .prefetch_related('details')
            .annotate(
                min_price=Min('details__price'),
                min_delivery_time=Min('details__delivery_time_in_days'),
            )
        )
        return self._apply_query_filters(queryset)

    def _apply_query_filters(self, queryset):
        params = self.request.query_params
        creator_id = params.get('creator_id')
        min_price = params.get('min_price')
        max_delivery_time = params.get('max_delivery_time')

        if creator_id not in (None, ''):
            queryset = self._filter_creator(queryset, creator_id)
        if min_price not in (None, ''):
            queryset = self._filter_min_price(queryset, min_price)
        if max_delivery_time not in (None, ''):
            queryset = self._filter_max_delivery_time(queryset, max_delivery_time)
        return queryset

    def _filter_creator(self, queryset, creator_id):
        try:
            return queryset.filter(user_id=int(creator_id))
        except ValueError:
            raise ValidationError({'creator_id': 'Muss eine gültige Ganzzahl sein.'})

    def _filter_min_price(self, queryset, min_price):
        try:
            return queryset.filter(min_price__gte=Decimal(min_price))
        except InvalidOperation:
            raise ValidationError({'min_price': 'Muss eine gültige Zahl sein.'})

    def _filter_max_delivery_time(self, queryset, max_delivery_time):
        try:
            return queryset.filter(min_delivery_time__lte=int(max_delivery_time))
        except ValueError:
            raise ValidationError({'max_delivery_time': 'Muss eine gültige Ganzzahl sein.'})

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OfferDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Endpunkt zum Abrufen, Aktualisieren und Löschen eines einzelnen Angebots."""

    permission_classes = [IsAuthenticated, IsOfferOwnerOrReadOnly]

    def get_queryset(self):
        return (
            Offer.objects.select_related('user')
            .prefetch_related('details')
            .annotate(
                min_price=Min('details__price'),
                min_delivery_time=Min('details__delivery_time_in_days'),
            )
        )

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return OfferWriteSerializer
        return OfferRetrieveSerializer


class OfferDetailItemView(generics.RetrieveAPIView):
    """Endpunkt zum Abrufen einer einzelnen Angebotsstufe anhand ihrer ID."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]

