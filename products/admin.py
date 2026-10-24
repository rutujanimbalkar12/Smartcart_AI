from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')  # Removed 'description'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'category', 'price', 'offer_type', 'stock_quantity')
    list_filter = ('store', 'category', 'offer_type')
    search_fields = ('name',)