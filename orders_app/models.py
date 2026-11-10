"""Database model for orders booked on an offer package tier."""

from django.db import models
from django.contrib.auth.models import User


class Order(models.Model):
    """An order booked by a customer on a package tier of a business user's offer.

    Price, delivery time and features are copied from the offer tier at booking
    time, so later changes to the offer do not alter existing orders.
    """

    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='customer_orders',
    )
    business_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='business_orders',
    )
    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return the order ID, title and status as its representation."""
        return f"Order #{self.id} - {self.title} ({self.status})"
