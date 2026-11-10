"""Tests for registration, login, profile detail and profile lists."""

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from .models import UserProfile


class AuthTests(APITestCase):
    """Test suite for user registration and authentication."""

    def setUp(self):
        """Create the auth endpoint URLs and one existing customer."""
        self.registration_url = reverse('registration')
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@mail.de',
            password='securepassword123',
        )
        UserProfile.objects.create(user=self.user, type='customer')

    def test_registration_customer_success(self):
        """Registering a customer returns a token and creates a customer profile."""
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
        """Registering a business user creates a business profile."""
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
        """Mismatching passwords are rejected with HTTP 400."""
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
        """An already registered email is rejected with HTTP 400."""
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
        """Missing required fields are rejected with HTTP 400."""
        data = {
            'username': 'incompleteuser',
            'password': 'password123',
        }
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Valid credentials return a token and the user ID."""
        data = {
            'username': 'existinguser',
            'password': 'securepassword123',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user_id'], self.user.id)

    def test_login_invalid_credentials(self):
        """Wrong credentials are rejected with HTTP 400."""
        data = {
            'username': 'existinguser',
            'password': 'wrongpassword',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password(self):
        """A missing password is rejected with HTTP 400."""
        data = {
            'username': 'existinguser',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileTests(APITestCase):
    """Test suite for single profiles and the customer and business lists."""

    def setUp(self):
        """Create one customer and one business user with profiles."""
        self.customer_user = User.objects.create_user(
            username='customer1',
            email='customer1@mail.de',
            password='password123',
            first_name='Max',
            last_name='Muster',
        )
        self.customer_profile = UserProfile.objects.create(
            user=self.customer_user,
            type='customer',
            location='Hamburg',
        )
        self.business_user = User.objects.create_user(
            username='business1',
            email='business1@mail.de',
            password='password123',
            first_name='Anna',
            last_name='Schmidt',
        )
        self.business_profile = UserProfile.objects.create(
            user=self.business_user,
            type='business',
            location='Berlin',
            working_hours='9-17',
        )
        self.detail_url = reverse('profile-detail', kwargs={'pk': self.business_user.id})
        self.business_list_url = reverse('profiles-business')
        self.customer_list_url = reverse('profiles-customer')

    def test_get_profile_authenticated_success(self):
        """An authenticated user can read another user's profile."""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'business1')
        self.assertEqual(response.data['first_name'], 'Anna')
        self.assertEqual(response.data['location'], 'Berlin')

    def test_get_profile_unauthenticated_fails(self):
        """Reading a profile without authentication returns HTTP 401."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_not_found(self):
        """Reading a non-existent profile returns HTTP 404."""
        self.client.force_authenticate(user=self.customer_user)
        url = reverse('profile-detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_own_profile_updates_user_and_profile(self):
        """Patching one's own profile updates both user and profile fields."""
        self.client.force_authenticate(user=self.business_user)
        data = {
            'first_name': 'Anna-Maria',
            'last_name': 'Becker',
            'email': 'anna.becker@mail.de',
            'location': 'München',
            'tel': '089123456',
            'description': 'Webdesign & SEO',
            'working_hours': '8-16',
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.business_user.refresh_from_db()
        self.business_profile.refresh_from_db()
        self.assertEqual(self.business_user.first_name, 'Anna-Maria')
        self.assertEqual(self.business_user.email, 'anna.becker@mail.de')
        self.assertEqual(self.business_profile.location, 'München')
        self.assertEqual(self.business_profile.tel, '089123456')

    def test_patch_other_profile_forbidden(self):
        """Patching another user's profile is forbidden."""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.patch(self.detail_url, {'location': 'Köln'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_business_profiles(self):
        """The business list contains only business profiles."""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.business_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'business1')
        self.assertEqual(response.data[0]['type'], 'business')

    def test_list_customer_profiles(self):
        """The customer list contains only customer profiles and exposes ``uploaded_at``."""
        self.client.force_authenticate(user=self.business_user)
        response = self.client.get(self.customer_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'customer1')
        self.assertIn('uploaded_at', response.data[0])

