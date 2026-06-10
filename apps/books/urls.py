from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.books.views import AuthorViewSet, BookViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='authors')
router.register(r'books', BookViewSet, basename='books')
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
]