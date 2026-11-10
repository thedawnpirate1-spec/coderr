"""Django admin registration for the reviews app."""

from django.contrib import admin
from .models import Review

admin.site.register(Review)
