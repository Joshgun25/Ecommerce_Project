from django.urls import path
from .views import ProductListView, ProductDetailView, CreateProductView, ActivateProductAPIView, AddCommentAPIView

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('create/', CreateProductView.as_view(), name='create-product'),
    path('activate/<str:token>/', ActivateProductAPIView.as_view(), name='activate-product'),
    path('api/product/<int:pk>/add-comment/', AddCommentAPIView.as_view(), name='add-comment'),
]
