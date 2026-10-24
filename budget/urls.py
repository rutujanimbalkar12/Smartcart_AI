from django.urls import path
from . import views

urlpatterns = [
    path('', views.budget_view, name='budget_view'),
    path('update/', views.update_budget, name='update_budget'),
]