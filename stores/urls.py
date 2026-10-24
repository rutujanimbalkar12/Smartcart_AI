from django.urls import path
from . import views

urlpatterns = [
    path('select/', views.store_selection, name='store_selection'),
    path('dashboard/', views.store_dashboard, name='store_dashboard'),
    path('locator/', views.store_locator_view, name='store_locator'),
]