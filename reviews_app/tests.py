"""Tests for customer reviews and the public base-info endpoint."""

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from profiles_app.models import UserProfile
from offers_app.models import Offer
from .models import Review


class ReviewAndBaseInfoTests(APITestCase):
    """Test suite for customer reviews and the public base-info endpoint."""

    def setUp(self):
        """Create business and customer users, one offer and two existing reviews."""
        self.business_user = User.objects.create_user(
            username='bizrev',
            email='bizrev@mail.de',
            password='password123',
        )
        UserProfile.objects.create(user=self.business_user, type='business')

        self.second_business = User.objects.create_user(
            username='bizrev2',
            email='bizrev2@mail.de',
            password='password123',
        )
        UserProfile.objects.create(user=self.second_business, type='business')

        self.customer_user = User.objects.create_user(
            username='custrev',
            email='custrev@mail.de',
            password='password123',
        )
        UserProfile.objects.create(user=self.customer_user, type='customer')

        self.second_customer = User.objects.create_user(
            username='custrev2',
            email='custrev2@mail.de',
            password='password123',
        )
        UserProfile.objects.create(user=self.second_customer, type='customer')

        Offer.objects.create(
            user=self.business_user,
            title='SEO Beratung',
            description='Technisches SEO Audit',
        )

        self.review = Review.objects.create(
            business_user=self.business_user,
            reviewer=self.customer_user,
            rating=5,
            description='Top Zusammenarbeit!',
        )
        Review.objects.create(
            business_user=self.business_user,
            reviewer=self.second_customer,
            rating=4,
            description='Sehr gut.',
        )

        self.list_url = reverse('review-list')
        self.detail_url = reverse('review-detail', kwargs={'pk': self.review.id})
        self.base_info_url = reverse('base-info')

    def test_list_reviews_and_filter(self):
        """Reviews can be filtered by reviewer."""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.list_url, {'reviewer_id': self.customer_user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['rating'], 5)

    def test_create_review_customer_success(self):
        """A customer can review a business user."""
        self.client.force_authenticate(user=self.customer_user)
        data = {
            'business_user': self.second_business.id,
            'rating': 4,
            'description': 'Schnelle Lieferung',
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['reviewer'], self.customer_user.id)

    def test_create_duplicate_review_fails(self):
        """A second review of the same business user is rejected."""
        self.client.force_authenticate(user=self.customer_user)
        data = {
            'business_user': self.business_user.id,
            'rating': 3,
            'description': 'Zweite Bewertung',
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_review_business_user_forbidden(self):
        """A business user cannot write a review."""
        self.client.force_authenticate(user=self.business_user)
        data = {
            'business_user': self.second_business.id,
            'rating': 5,
            'description': 'Kollegenbewertung',
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_and_delete_review_permissions(self):
        """Only the author can patch or delete a review."""
        self.client.force_authenticate(user=self.second_customer)
        forbidden_patch = self.client.patch(self.detail_url, {'rating': 1}, format='json')
        self.assertEqual(forbidden_patch.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.customer_user)
        ok_patch = self.client.patch(
            self.detail_url,
            {'rating': 3, 'description': 'Korrigierte Bewertung'},
            format='json',
        )
        self.assertEqual(ok_patch.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 3)

        del_resp = self.client.delete(self.detail_url)
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_base_info_public_and_accurate(self):
        """The public base-info endpoint returns accurate statistics."""
        response = self.client.get(self.base_info_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['review_count'], 2)
        self.assertEqual(response.data['average_rating'], 4.5)
        self.assertEqual(response.data['business_profile_count'], 2)
        self.assertEqual(response.data['offer_count'], 1)
