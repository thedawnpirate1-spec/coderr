"""Database model for customer reviews of business users."""

from django.db import models
from django.contrib.auth.models import User


class Review(models.Model):
    """A rating and comment a customer gives to a business user.

    Each reviewer may review a given business user only once.
    """

    business_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_reviews',
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='written_reviews',
    )
    rating = models.PositiveSmallIntegerField()
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model options: one review per (business user, reviewer) pair."""

        constraints = [
            models.UniqueConstraint(
                fields=['business_user', 'reviewer'],
                name='unique_review_per_business_and_reviewer',
            )
        ]

    def __str__(self):
        """Return the rating, reviewer and reviewed user as its representation."""
        return f"Review ({self.rating}*) by {self.reviewer.username} for {self.business_user.username}"
