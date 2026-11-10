"""Django admin registration for the orders app."""

from django.contrib import admin
from .models import Order

admin.site.register(Order)
