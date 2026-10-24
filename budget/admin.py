from django.contrib import admin
from .models import Budget

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['customer', 'amount', 'updated_at']
    search_fields = ['customer__username']