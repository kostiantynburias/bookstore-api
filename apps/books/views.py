from django.db import transaction
from django.db.models import Avg, Count
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from apps.books.models import (
    Author,
    Book,
    Order,
    OrderItem
)
from apps.books.serializers import (
    AuthorSerializer,
    BookSerializer,
    OrderSerializer,
    CheckoutOrderSerializer
)
from apps.books.permissions import IsAdminOrReadOnly
from apps.books.tasks import send_order_confirmation_email


class AuthorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing authors.
    Read access is available to everyone, write access restricted to admins.
    Queryset is annotated with books_count and average_book_price aggregations.
    """
    
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Return authors annotated with book count and average book price."""
        queryset = Author.objects.annotate(
            books_count=Count('books'),
            average_book_price=Avg('books__price')
        )
        return queryset


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing books.
    Read access is available to everyone, write access restricted to admins.
    Queryset uses select_related to avoid N+1 problem on author field.
    """

    queryset = Book.objects.select_related('author')
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['author']
    search_fields = ['title'] 


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders.
    Authenticated users can only view and create their own orders.
    Admins can view and modify all orders.
    """
    
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return orders based on user role."""
        if self.request.user.is_staff:
            return Order.objects.prefetch_related('order_items__book', 'user')
        return Order.objects.prefetch_related('order_items__book', 'user').filter(user=self.request.user)
    
    def get_permissions(self):
        """
        Dynamically determine the permissions required for the current action.
        
        Restricts data-modifying actions (update, partial_update, destroy) 
        to staff/admin users only. Other actions inherit the default 
        permission classes (e.g., IsAuthenticated).
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """
        POST /api/v1/orders/checkout/
        Create a new order from a list of books and quantities.
        Validates stock availability and deducts stock atomically.
        Returns 201 with order data on success, 400 if stock is insufficient.
        """
        serializer = CheckoutOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            order = Order.objects.create(user=request.user)

            total_price = 0
            for item in serializer.validated_data['items']:
                try:
                    book = Book.objects.select_for_update().get(id=item['book'])
                except Book.DoesNotExist:
                    raise serializers.ValidationError({"error": f"Книгу з ID {item['book']} не знайдено."})

                if book.stock < item['quantity']:
                    raise serializers.ValidationError(
                        {"stock": f"Недостатньо товару '{book.title}'. Доступно: {book.stock}."}
                    )
                book.stock -= item['quantity']
                book.save()

                order_item = OrderItem.objects.create(
                    order=order,
                    book=book,
                    quantity=item['quantity'],
                    price=book.price # Snapshot price at the time of purchase
                )

                total_price += order_item.calculate_total_price()

            order.total_price = total_price
            order.save()

        send_order_confirmation_email.delay(order_id=order.id)

        full_order = Order.objects.prefetch_related('order_items__book', 'user').get(id=order.id)
        return Response(OrderSerializer(full_order).data, status=status.HTTP_201_CREATED)