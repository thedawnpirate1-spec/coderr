from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from profiles_app.models import UserProfile
from offers_app.models import Offer, OfferDetail
from .models import Order


class OrderTests(APITestCase):
    """Testsuite für Bestellungen, Status-Updates, Staff-Löschung und Auftragszähler."""

    def setUp(self):
        self.business_user = User.objects.create_user(
            username='bizorder',
            email='bizorder@mail.de',
            password='password123',
        )
        UserProfile.objects.create(user=self.business_user, type='business')

        self.customer_user = User.objects.create_user(
            username='custorder',
            email='custorder@mail.de',
            password='password123',
        )
        UserProfile.objects.create(user=self.customer_user, type='customer')

        self.staff_user = User.objects.create_user(
            username='adminuser',
            email='admin@mail.de',
            password='password123',
            is_staff=True,
        )
        UserProfile.objects.create(user=self.staff_user, type='customer')

        self.offer = Offer.objects.create(
            user=self.business_user,
            title='App Entwicklung',
            description='Cross-Platform App',
        )
        self.offer_detail = OfferDetail.objects.create(
            offer=self.offer,
            title='Standard App',
            revisions=3,
            delivery_time_in_days=14,
            price=1200.00,
            features=['iOS', 'Android'],
            offer_type='standard',
        )
        self.order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user,
            title='Bestehende Bestellung',
            revisions=2,
            delivery_time_in_days=7,
            price=500.00,
            features=['Design'],
            offer_type='basic',
            status='in_progress',
        )

        self.list_url = reverse('order-list')
        self.detail_url = reverse('order-detail', kwargs={'pk': self.order.id})
        self.count_url = reverse('order-count', kwargs={'business_user_id': self.business_user.id})
        self.completed_count_url = reverse(
            'completed-order-count',
            kwargs={'business_user_id': self.business_user.id},
        )

    def test_list_orders_authenticated(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Bestehende Bestellung')

    def test_create_order_customer_snapshots_offerdetail(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.list_url, {'offer_detail_id': self.offer_detail.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Standard App')
        self.assertEqual(response.data['price'], 1200.0)
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(response.data['business_user'], self.business_user.id)

    def test_create_order_business_user_forbidden(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.post(self.list_url, {'offer_detail_id': self.offer_detail.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_nonexistent_offerdetail_returns_404(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.list_url, {'offer_detail_id': 9999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_order_status_by_business_user(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.patch(self.detail_url, {'status': 'completed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'completed')

    def test_patch_order_by_customer_forbidden(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.patch(self.detail_url, {'status': 'completed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_order_invalid_status_returns_400(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.patch(self.detail_url, {'status': 'unknown'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_order_only_staff_allowed(self):
        self.client.force_authenticate(user=self.business_user)
        forbidden_resp = self.client.delete(self.detail_url)
        self.assertEqual(forbidden_resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.staff_user)
        ok_resp = self.client.delete(self.detail_url)
        self.assertEqual(ok_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(id=self.order.id).exists())

    def test_order_counts_and_404_for_non_business(self):
        self.client.force_authenticate(user=self.customer_user)
        in_prog_resp = self.client.get(self.count_url)
        self.assertEqual(in_prog_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(in_prog_resp.data['order_count'], 1)

        comp_resp = self.client.get(self.completed_count_url)
        self.assertEqual(comp_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(comp_resp.data['completed_order_count'], 0)

        non_biz_url = reverse('order-count', kwargs={'business_user_id': self.customer_user.id})
        not_found_resp = self.client.get(non_biz_url)
        self.assertEqual(not_found_resp.status_code, status.HTTP_404_NOT_FOUND)
