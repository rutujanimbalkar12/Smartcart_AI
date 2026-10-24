from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_management, name='list_management'),
    path('<int:list_id>/', views.list_detail, name='list_detail'),
    path('item/delete/<int:item_id>/', views.delete_list_item, name='delete_list_item'),
]