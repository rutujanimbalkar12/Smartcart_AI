from django.db import models
from django.conf import settings
from products.models import Product

class ShoppingList(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shopping_lists')
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_estimated_cost(self):
        return sum(item.subtotal() for item in self.items.all())

    def __str__(self):
        return f"{self.name} ({self.customer.username})"

class ListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    custom_item_name = models.CharField(max_length=150, blank=True, help_text="For planning items not yet in inventory")
    quantity = models.PositiveIntegerField(default=1)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def subtotal(self):
        return self.quantity * self.estimated_price

    def __str__(self):
        name = self.product.name if self.product else self.custom_item_name
        return f"{name} ({self.quantity})"