from django.db import models

class Store(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)
    opening_hours = models.CharField(max_length=100, default="8:00 AM - 10:00 PM")
    distance_km = models.DecimalField(max_digits=5, decimal_places=2, default=1.2, help_text="Distance in km")

    def __str__(self):
        return self.name