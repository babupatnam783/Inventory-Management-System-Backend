
from django.urls import path
from .views import InventoryAPIView,ProductAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [

    path('items/', InventoryAPIView.as_view(), name='inventory'),
    path('items/<int:item_id>/', InventoryAPIView.as_view(), name='inventory-detail'),
    path('items/<int:item_id>/<str:action>', InventoryAPIView.as_view(), name='inventory-detail'),

    path('products/', ProductAPIView.as_view(), name='product-list'),
    path('products/<int:product_id>', ProductAPIView.as_view(), name='product-detail'),

]