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
    """Endpunkt zum Auflisten eigener Bestellungen und zum Erstellen einer neuen Bestellung."""

    permission_classes = [IsCustomerForPostOrAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(Q(customer_user=user) | Q(business_user=user))

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Endpunkt zum Aktualisieren des Bestellstatus durch Anbieter oder Löschen durch Staff."""

    queryset = Order.objects.all()
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [IsOrderBusinessOrStaffDelete]


class OrderCountView(APIView):
    """Endpunkt zur Ermittlung der Anzahl laufender Bestellungen eines Business-Nutzers."""

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id):
        get_object_or_404(User, pk=business_user_id, profile__type='business')
        count = Order.objects.filter(
            business_user_id=business_user_id,
            status='in_progress',
        ).count()
        return Response({'order_count': count}, status=status.HTTP_200_OK)


class CompletedOrderCountView(APIView):
    """Endpunkt zur Ermittlung der Anzahl abgeschlossener Bestellungen eines Business-Nutzers."""

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id):
        get_object_or_404(User, pk=business_user_id, profile__type='business')
        count = Order.objects.filter(
            business_user_id=business_user_id,
            status='completed',
        ).count()
        return Response({'completed_order_count': count}, status=status.HTTP_200_OK)

