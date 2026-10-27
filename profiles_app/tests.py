from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from .models import UserProfile


class AuthTests(APITestCase):
    """Testsuite für Benutzer-Registrierung und Authentifizierung."""

    def setUp(self):
        self.registration_url = reverse('registration')
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@mail.de',
            password='securepassword123',
        )
        UserProfile.objects.create(user=self.user, type='customer')

    def test_registration_customer_success(self):
        data = {
            'username': 'newcustomer',
            'email': 'customer@mail.de',
            'password': 'password123',
            'repeated_password': 'password123',
            'type': 'customer',
        }
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'newcustomer')
        self.assertTrue(UserProfile.objects.filter(user__username='newcustomer', type='customer').exists())

    def test_registration_business_success(self):
        data = {
            'username': 'newbusiness',
            'email': 'business@mail.de',
            'password': 'password123',
            'repeated_password': 'password123',
            'type': 'business',
        }
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'business@mail.de')
        self.assertTrue(UserProfile.objects.filter(user__username='newbusiness', type='business').exists())

    def test_registration_password_mismatch(self):
        data = {
            'username': 'failuser',
            'email': 'fail@mail.de',
            'password': 'password123',
            'repeated_password': 'differentpassword',
            'type': 'customer',
        }
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('repeated_password', response.data)

    def test_registration_duplicate_email(self):
        data = {
            'username': 'anotheruser',
            'email': 'existing@mail.de',
            'password': 'password123',
            'repeated_password': 'password123',
            'type': 'customer',
        }
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_missing_field(self):
        data = {
            'username': 'incompleteuser',
            'password': 'password123',
        }
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        data = {
            'username': 'existinguser',
            'password': 'securepassword123',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user_id'], self.user.id)

    def test_login_invalid_credentials(self):
        data = {
            'username': 'existinguser',
            'password': 'wrongpassword',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password(self):
        data = {
            'username': 'existinguser',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
