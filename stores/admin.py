from django.contrib import admin
from .models import Store

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'opening_hours', 'distance_km')
    search_fields = ('name', 'address')