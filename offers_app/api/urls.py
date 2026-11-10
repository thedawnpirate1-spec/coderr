"""URL routes of the offers API."""

from django.urls import path
from .views import OfferDetailItemView, OfferDetailView, OfferListCreateView

urlpatterns = [
    path('offers/', OfferListCreateView.as_view(), name='offer-list'),
    path('offers/<int:pk>/', OfferDetailView.as_view(), name='offer-detail'),
    path('offerdetails/<int:pk>/', OfferDetailItemView.as_view(), name='offerdetail-detail'),
]
