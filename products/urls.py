from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('cart/', lambda request: redirect('/cart/')),
    path('cart/add/<int:product_id>/', lambda request, product_id: redirect(f'/cart/add/{product_id}/')),
    path('ai-assistant/', views.ai_assistant_view, name='ai_assistant'),
    path('budget-optimizer/', views.budget_optimizer_view, name='budget_optimizer'),
    path('plan-shopping/', views.plan_shopping_view, name='plan_shopping'),
    path('compare/', views.price_comparison_view, name='price_comparison'),
    path('cart-compare/', views.cart_comparison_view, name='cart_comparison'),
    path('history/', views.shopping_history_view, name='shopping_history'),
    path('scan-bill/', views.bill_scanner_view, name='bill_scanner'),
    path('analytics/', views.spending_analytics_view, name='spending_analytics'),
    path('insights/', views.spending_insights_view, name='spending_insights'),
    path('agent/', views.advanced_ai_agent_view, name='advanced_agent'),
    path('barcode-scanner/', views.barcode_scanner_view, name='barcode_scanner'),
    path('smart-recommendations/', views.smart_recommendations_view, name='smart_recommendations'),
]