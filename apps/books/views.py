from django.db import transaction
from django.db.models import Avg, Count
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from drf_spectacular.utils import (
    extend_schema, 
    extend_schema_view, 
    OpenApiResponse, 
    OpenApiExample
)

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


@extend_schema(tags=['Authors'])
@extend_schema_view(
    list=extend_schema(summary="List authors with aggregations", description="Returns a list of authors annotated with books count and average book price."),
    retrieve=extend_schema(summary="Retrieve author details", description="Returns detailed profile of an author including aggregated stats."),
    create=extend_schema(summary="Create a new author (Admin only)"),
    update=extend_schema(summary="Update an author completely (Admin only)"),
    partial_update=extend_schema(summary="Patch author fields (Admin only)"),
    destroy=extend_schema(summary="Delete an author (Admin only)")
)
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
        ).order_by('id')
        return queryset


@extend_schema(tags=['Books'])
@extend_schema_view(
    list=extend_schema(summary="List books with filters", description="Get books. Supports searching by title and filtering by author ID."),
    retrieve=extend_schema(summary="Get specific book details"),
    create=extend_schema(summary="Create a new book (Admin only)"),
    update=extend_schema(summary="Update a book completely (Admin only)"),
    partial_update=extend_schema(summary="Patch book fields (Admin only)"),
    destroy=extend_schema(summary="Delete a book (Admin only)")
)
class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing books.
    Read access is available to everyone, write access restricted to admins.
    Queryset uses select_related to avoid N+1 problem on author field.
    """

    queryset = Book.objects.select_related('author').order_by('id')
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['author']
    search_fields = ['title'] 


@extend_schema(tags=['Orders'])
@extend_schema_view(
    list=extend_schema(summary="List orders", description="Regular users see only their own orders. Staff members see all orders in the system."),
    retrieve=extend_schema(summary="Get order details", description="Staff or order owner only."),
    create=extend_schema(
        summary="Create order manually (Disabled)", 
        deprecated=True, 
        description="Direct order creation is disabled to prevent stock desynchronization. Use /checkout/ endpoint instead."
    ),
    update=extend_schema(summary="Update order (Admin only)"),
    partial_update=extend_schema(summary="Patch order fields (Admin only)"),
    destroy=extend_schema(summary="Cancel/Delete order (Admin only)")
)
class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders.
    Authenticated users can only view their own orders and create them via /checkout/.
    Admins can view and modify statuses/orders, but direct creation is disabled.
    """
    
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return orders based on user role."""
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()

        if self.request.user.is_staff:
            return Order.objects.prefetch_related('order_items__book', 'user')
        return Order.objects.prefetch_related('order_items__book', 'user').filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return the appropriate serializer class based on the action."""
        if self.action == 'checkout':
            return CheckoutOrderSerializer
        return OrderSerializer
    
    def get_permissions(self):
        """
        Restricts modifying actions strictly to staff/admin users.
        Standard creation (POST) is handled by the create() method rejection.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Mutes the standard POST /api/v1/orders/ endpoint.
        Forces everyone (including admins) to use the atomic /checkout/ process.
        """
        return Response(
            {"detail": "Method \"POST\" on this endpoint is disabled. Use /checkout/ instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    @extend_schema(
        summary="Process cart checkout",
        description="Creates a real order with items from the shopping cart. Validates stock availability atomically, updates warehouse and triggers an email notification.",
        request=CheckoutOrderSerializer,
        responses={
            201: OpenApiResponse(
                response=OrderSerializer,
                description="Order successfully placed and processed.",
                examples=[
                    OpenApiExample(
                        name="Successful Checkout Response",
                        value={
                            "id": 105,
                            "user": 3,
                            "total_price": "850.00",
                            "order_items": [
                                {
                                    "id": 210,
                                    "book": {
                                        "id": 14,
                                        "title": "Clean Code",
                                        "price": "450.00"
                                    },
                                    "quantity": 1,
                                    "price": "450.00"
                                }
                            ],
                            "created_at": "2026-06-09T17:34:00Z"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Validation error (e.g., requested quantity exceeds stock limit or book ID does not exist)."
            )
        }
    )
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """
        POST /api/v1/orders/checkout/
        Create a new order from a list of books and quantities.
        Validates stock availability and deducts stock atomically.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            order = Order.objects.create(user=request.user)

            total_price = 0
            for item in serializer.validated_data['items']:
                book = Book.objects.select_for_update().get(pk=item['book'].pk)

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
                    price=book.price
                )

                total_price += order_item.calculate_total_price()

            order.total_price = total_price
            order.save()

        send_order_confirmation_email.delay(order_id=order.id)

        full_order = Order.objects.prefetch_related('order_items__book', 'user').get(id=order.id)
        return Response(OrderSerializer(full_order).data, status=status.HTTP_201_CREATED)