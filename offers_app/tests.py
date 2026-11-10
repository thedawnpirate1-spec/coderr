"""Tests for offers, package tiers, filtering, search and permissions."""

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from profiles_app.models import UserProfile
from .models import Offer, OfferDetail


class OfferTests(APITestCase):
    """Test suite for offers, package tiers, filters, search and permissions."""

    def setUp(self):
        """Create business, customer and other users plus one offer with three tiers."""
        self.business_user = User.objects.create_user(
            username='bizuser',
            email='biz@mail.de',
            password='password123',
        )
        UserProfile.objects.create(user=self.business_user, type='business')

        self.other_business = User.objects.create_user(
            username='otherbiz',
            email='otherbiz@mail.de',
            password='password123',
        )
        UserProfile.objects.create(user=self.other_business, type='business')

        self.customer_user = User.objects.create_user(
            username='custuser',
            email='cust@mail.de',
            password='password123',
        )
        UserProfile.objects.create(user=self.customer_user, type='customer')

        self.offer = Offer.objects.create(
            user=self.business_user,
            title='Webdesign Paket',
            description='Moderne Landingpage mit Django',
        )
        self.detail_basic = OfferDetail.objects.create(
            offer=self.offer,
            title='Basic',
            revisions=2,
            delivery_time_in_days=5,
            price=150.00,
            features=['1 Seite'],
            offer_type='basic',
        )
        OfferDetail.objects.create(
            offer=self.offer,
            title='Standard',
            revisions=5,
            delivery_time_in_days=7,
            price=300.00,
            features=['3 Seiten', 'SEO'],
            offer_type='standard',
        )
        OfferDetail.objects.create(
            offer=self.offer,
            title='Premium',
            revisions=-1,
            delivery_time_in_days=10,
            price=600.00,
            features=['5 Seiten', 'SEO', 'Hosting'],
            offer_type='premium',
        )

        self.list_url = reverse('offer-list')
        self.detail_url = reverse('offer-detail', kwargs={'pk': self.offer.id})
        self.offerdetail_url = reverse('offerdetail-detail', kwargs={'pk': self.detail_basic.id})

    def _valid_offer_payload(self):
        """Return a valid payload for creating an offer with all three tiers."""
        return {
            'title': 'Logo Design',
            'description': 'Professionelles Vektor-Logo',
            'details': [
                {
                    'title': 'Basic Logo',
                    'revisions': 1,
                    'delivery_time_in_days': 3,
                    'price': 80,
                    'features': ['PNG'],
                    'offer_type': 'basic',
                },
                {
                    'title': 'Standard Logo',
                    'revisions': 3,
                    'delivery_time_in_days': 5,
                    'price': 160,
                    'features': ['PNG', 'SVG'],
                    'offer_type': 'standard',
                },
                {
                    'title': 'Premium Logo',
                    'revisions': -1,
                    'delivery_time_in_days': 7,
                    'price': 320,
                    'features': ['PNG', 'SVG', 'Brandguide'],
                    'offer_type': 'premium',
                },
            ],
        }

    def test_list_offers_public_and_paginated(self):
        """Anyone can list offers; the response is paginated and includes minimum values."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['min_price'], 150.0)
        self.assertEqual(response.data['results'][0]['min_delivery_time'], 5)

    def test_list_offers_filters_and_search(self):
        """The creator, price, delivery time and search filters narrow the result."""
        response = self.client.get(self.list_url, {'creator_id': self.business_user.id, 'min_price': 100})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        empty_resp = self.client.get(self.list_url, {'max_delivery_time': 2})
        self.assertEqual(empty_resp.data['count'], 0)

        search_resp = self.client.get(self.list_url, {'search': 'Landingpage'})
        self.assertEqual(search_resp.data['count'], 1)

    def test_list_offers_invalid_filter_returns_400(self):
        """A non-numeric filter value is rejected with HTTP 400."""
        response = self.client.get(self.list_url, {'max_delivery_time': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_business_user_success(self):
        """A business user can create an offer with three tiers."""
        self.client.force_authenticate(user=self.business_user)
        response = self.client.post(self.list_url, self._valid_offer_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['details']), 3)
        self.assertEqual(Offer.objects.count(), 2)

    def test_create_offer_customer_forbidden(self):
        """A customer cannot create an offer."""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.list_url, self._valid_offer_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_offer_missing_detail_tier_fails(self):
        """Creating an offer with fewer than three tiers fails with HTTP 400."""
        self.client.force_authenticate(user=self.business_user)
        payload = self._valid_offer_payload()
        payload['details'].pop()
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_offer_requires_authentication(self):
        """Retrieving a single offer requires authentication."""
        unauth_resp = self.client.get(self.detail_url)
        self.assertEqual(unauth_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.customer_user)
        auth_resp = self.client.get(self.detail_url)
        self.assertEqual(auth_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(auth_resp.data['title'], 'Webdesign Paket')

    def test_patch_offer_owner_updates_detail(self):
        """The owner can patch an offer and one of its tiers."""
        self.client.force_authenticate(user=self.business_user)
        patch_data = {
            'title': 'Webdesign Pro Paket',
            'details': [
                {
                    'title': 'Basic Neu',
                    'revisions': 3,
                    'delivery_time_in_days': 4,
                    'price': 199,
                    'features': ['1 Seite', 'Kontaktformular'],
                    'offer_type': 'basic',
                }
            ],
        }
        response = self.client.patch(self.detail_url, patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.detail_basic.refresh_from_db()
        self.assertEqual(float(self.detail_basic.price), 199.0)
        self.assertEqual(self.detail_basic.title, 'Basic Neu')

    def test_patch_and_delete_offer_other_user_forbidden(self):
        """A user who does not own the offer cannot patch or delete it."""
        self.client.force_authenticate(user=self.other_business)
        patch_resp = self.client.patch(self.detail_url, {'title': 'Hack'}, format='json')
        self.assertEqual(patch_resp.status_code, status.HTTP_403_FORBIDDEN)

        del_resp = self.client.delete(self.detail_url)
        self.assertEqual(del_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_offer_owner_success(self):
        """The owner can delete an offer."""
        self.client.force_authenticate(user=self.business_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Offer.objects.filter(id=self.offer.id).exists())

    def test_retrieve_offerdetail_authenticated(self):
        """An authenticated user can retrieve a single package tier."""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.offerdetail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['offer_type'], 'basic')
