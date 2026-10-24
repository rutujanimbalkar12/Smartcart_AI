from django.db import models
from stores.models import Store

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    OFFER_CHOICES = [
        ('NONE', 'No Offer'),
        ('PERCENTAGE', 'Percentage Discount'),
        ('FLAT', 'Flat Discount'),
        ('B1G1', 'Buy 1 Get 1'),
        ('LIMITED', 'Limited-time Offer'),
        ('CATEGORY', 'Category Offer'),
    ]

    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Original Price")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Discount %")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Flat Discount amount")
    offer_type = models.CharField(max_length=20, choices=OFFER_CHOICES, default='NONE')
    offer_description = models.CharField(max_length=255, blank=True, null=True)
    stock_quantity = models.IntegerField(default=0)
    unit = models.CharField(max_length=50, default='pcs')
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def get_final_price(self):
        original = float(self.price)
        if self.offer_type == 'PERCENTAGE' and self.discount_percentage > 0:
            return round(original * (1 - float(self.discount_percentage) / 100), 2)
        elif self.offer_type == 'FLAT' and self.discount_amount > 0:
            return round(max(0.0, original - float(self.discount_amount)), 2)
        return original

    def __str__(self):
        return f"{self.name} - ₹{self.get_final_price()}"

class PastOrder(models.Model):
    customer = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='past_orders',
    )
    store_name = models.CharField(max_length=100)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    items_summary = models.TextField(help_text="Comma-separated list of items bought")

    def __str__(self):
        return f"{self.store_name} - ₹{self.total_amount} ({self.date})"