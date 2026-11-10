"""API views for creating, listing and managing orders and order counters."""

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import Order
from .permissions import IsCustomerForPostOrAuthenticated, IsOrderBusinessOrStaffDelete
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
)


class OrderListCreateView(generics.ListCreateAPIView):
    """Endpoint to list the user's own orders and to create a new order."""

    permission_classes = [IsCustomerForPostOrAuthenticated]

    def get_queryset(self):
        """Return the orders in which the requesting user is customer or business user."""
        user = self.request.user
        return Order.objects.filter(Q(customer_user=user) | Q(business_user=user))

    def get_serializer_class(self):
        """Return the create serializer for POST requests, the read serializer otherwise."""
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Endpoint for the business user to update an order's status or for staff to delete it."""

    queryset = Order.objects.all()
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [IsOrderBusinessOrStaffDelete]


class OrderCountView(APIView):
    """Endpoint returning the number of in-progress orders of a business user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id):
        """Count the in-progress orders of a business user.

        Args:
            request: The incoming DRF request.
            business_user_id: ID of the business user.

        Returns:
            A response containing ``order_count``.

        Raises:
            Http404: If no business user with this ID exists.
        """
        get_object_or_404(User, pk=business_user_id, profile__type='business')
        count = Order.objects.filter(
            business_user_id=business_user_id,
            status='in_progress',
        ).count()
        return Response({'order_count': count}, status=status.HTTP_200_OK)


class CompletedOrderCountView(APIView):
    """Endpoint returning the number of completed orders of a business user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id):
        """Count the completed orders of a business user.

        Args:
            request: The incoming DRF request.
            business_user_id: ID of the business user.

        Returns:
            A response containing ``completed_order_count``.

        Raises:
            Http404: If no business user with this ID exists.
        """
        get_object_or_404(User, pk=business_user_id, profile__type='business')
        count = Order.objects.filter(
            business_user_id=business_user_id,
            status='completed',
        ).count()
        return Response({'completed_order_count': count}, status=status.HTTP_200_OK)
