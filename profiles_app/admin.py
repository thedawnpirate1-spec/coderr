"""Django admin registration for the profiles app."""

from django.contrib import admin
from .models import UserProfile

admin.site.register(UserProfile)
