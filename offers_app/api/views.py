"""API views for listing, creating and managing offers and their package tiers."""

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
    """Pagination for the offer list with 6 entries per page by default."""

    page_size = 6
    page_size_query_param = 'page_size'


class OfferListCreateView(generics.ListCreateAPIView):
    """Endpoint to list, filter, search and create offers."""

    permission_classes = [IsBusinessUserOrReadOnly]
    pagination_class = OfferPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        """Return the write serializer for POST requests, the list serializer otherwise."""
        if self.request.method == 'POST':
            return OfferWriteSerializer
        return OfferListSerializer

    def get_queryset(self):
        """Build the offer queryset with minimum price and delivery time annotations.

        Returns:
            A queryset of offers with the query-string filters applied.
        """
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
        """Apply the optional ``creator_id``, ``min_price`` and ``max_delivery_time`` filters.

        Args:
            queryset: The base offer queryset.

        Returns:
            The filtered queryset.

        Raises:
            ValidationError: If a filter value cannot be parsed.
        """
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
        """Restrict the queryset to offers of one creator.

        Args:
            queryset: The offer queryset.
            creator_id: The creator's user ID as a string.

        Returns:
            The filtered queryset.

        Raises:
            ValidationError: If ``creator_id`` is not an integer.
        """
        try:
            return queryset.filter(user_id=int(creator_id))
        except ValueError:
            raise ValidationError({'creator_id': 'Muss eine gültige Ganzzahl sein.'})

    def _filter_min_price(self, queryset, min_price):
        """Keep only offers whose cheapest tier costs at least ``min_price``.

        Args:
            queryset: The offer queryset (annotated with ``min_price``).
            min_price: The price threshold as a string.

        Returns:
            The filtered queryset.

        Raises:
            ValidationError: If ``min_price`` is not a valid number.
        """
        try:
            return queryset.filter(min_price__gte=Decimal(min_price))
        except InvalidOperation:
            raise ValidationError({'min_price': 'Muss eine gültige Zahl sein.'})

    def _filter_max_delivery_time(self, queryset, max_delivery_time):
        """Keep only offers whose fastest tier is delivered within ``max_delivery_time`` days.

        Args:
            queryset: The offer queryset (annotated with ``min_delivery_time``).
            max_delivery_time: The maximum number of days as a string.

        Returns:
            The filtered queryset.

        Raises:
            ValidationError: If ``max_delivery_time`` is not an integer.
        """
        try:
            return queryset.filter(min_delivery_time__lte=int(max_delivery_time))
        except ValueError:
            raise ValidationError({'max_delivery_time': 'Muss eine gültige Ganzzahl sein.'})

    def perform_create(self, serializer):
        """Save the new offer with the requesting user as its owner."""
        serializer.save(user=self.request.user)


class OfferDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Endpoint to retrieve, update and delete a single offer."""

    permission_classes = [IsAuthenticated, IsOfferOwnerOrReadOnly]

    def get_queryset(self):
        """Return all offers annotated with minimum price and delivery time."""
        return (
            Offer.objects.select_related('user')
            .prefetch_related('details')
            .annotate(
                min_price=Min('details__price'),
                min_delivery_time=Min('details__delivery_time_in_days'),
            )
        )

    def get_serializer_class(self):
        """Return the write serializer for PUT/PATCH requests, the retrieve serializer otherwise."""
        if self.request.method in ('PUT', 'PATCH'):
            return OfferWriteSerializer
        return OfferRetrieveSerializer


class OfferDetailItemView(generics.RetrieveAPIView):
    """Endpoint to retrieve a single offer package tier by its ID."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]
