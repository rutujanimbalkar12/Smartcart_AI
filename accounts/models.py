from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        STORE_OWNER = 'STORE_OWNER', 'Store Owner'
        ADMIN = 'ADMIN', 'Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        help_text="Designates role privileges across the platform."
    )

    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    def is_store_owner(self):
        return self.role == self.Role.STORE_OWNER


class CustomerProfile(models.Model):
    customer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    preferred_area = models.CharField(max_length=150, blank=True)
    preferred_store = models.ForeignKey(
        'stores.Store',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_by_customers',
    )
    preferred_categories = models.JSONField(default=list, blank=True)
    budget_alert_threshold = models.PositiveSmallIntegerField(default=80)
    budget_alerts = models.BooleanField(default=True)
    shopping_reminders = models.BooleanField(default=True)
    offers_notifications = models.BooleanField(default=True)
    price_change_notifications = models.BooleanField(default=False)
    ai_recommendations = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.customer.username}"