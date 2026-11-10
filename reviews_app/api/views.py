"""API views for customer reviews and general platform statistics."""

from django.db.models import Avg
from rest_framework import filters, generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from offers_app.models import Offer
from profiles_app.models import UserProfile
from ..models import Review
from .permissions import IsCustomerOrReadOnlyAuthenticated, IsReviewAuthorOrReadOnly
from .serializers import ReviewSerializer, ReviewUpdateSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    """Endpoint to list, filter and create customer reviews."""

    serializer_class = ReviewSerializer
    permission_classes = [IsCustomerOrReadOnlyAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['updated_at', 'rating']
    ordering = ['-updated_at']

    def get_queryset(self):
        """Return the reviews, optionally filtered by ``business_user_id`` and ``reviewer_id``.

        Returns:
            The filtered review queryset.

        Raises:
            ValidationError: If a filter value is not an integer.
        """
        queryset = Review.objects.all()
        params = self.request.query_params
        business_user_id = params.get('business_user_id')
        reviewer_id = params.get('reviewer_id')

        if business_user_id not in (None, ''):
            try:
                queryset = queryset.filter(business_user_id=int(business_user_id))
            except ValueError:
                raise ValidationError({'business_user_id': 'Muss eine gültige Ganzzahl sein.'})

        if reviewer_id not in (None, ''):
            try:
                queryset = queryset.filter(reviewer_id=int(reviewer_id))
            except ValueError:
                raise ValidationError({'reviewer_id': 'Muss eine gültige Ganzzahl sein.'})

        return queryset

    def perform_create(self, serializer):
        """Save the new review with the requesting user as its reviewer."""
        serializer.save(reviewer=self.request.user)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Endpoint for a review's author to retrieve, update or delete the review."""

    queryset = Review.objects.all()
    serializer_class = ReviewUpdateSerializer
    permission_classes = [IsReviewAuthorOrReadOnly]


class BaseInfoView(APIView):
    """Public endpoint providing general platform statistics for the start page."""

    permission_classes = [AllowAny]

    def get(self, request):
        """Collect the platform statistics.

        Args:
            request: The incoming DRF request.

        Returns:
            A response with ``review_count``, ``average_rating`` (rounded to one
            decimal, 0.0 without reviews), ``business_profile_count`` and ``offer_count``.
        """
        review_count = Review.objects.count()
        avg_val = Review.objects.aggregate(avg_rating=Avg('rating'))['avg_rating']
        average_rating = round(float(avg_val), 1) if avg_val is not None else 0.0
        business_profile_count = UserProfile.objects.filter(type='business').count()
        offer_count = Offer.objects.count()

        return Response(
            {
                'review_count': review_count,
                'average_rating': average_rating,
                'business_profile_count': business_profile_count,
                'offer_count': offer_count,
            },
            status=status.HTTP_200_OK,
        )
