from django.contrib import admin
from .models import ShoppingList, ListItem

class ListItemInline(admin.TabularInline):
    model = ListItem
    extra = 1

@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ['name', 'customer', 'created_at', 'total_estimated_cost']
    search_fields = ['name', 'customer__username']
    inlines = [ListItemInline]