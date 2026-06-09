from rest_framework import serializers

from apps.books.models import (
    Author,
    Book,
    Order,
    OrderItem
)


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for Author model with aggregated fields."""

    books_count = serializers.IntegerField(read_only=True)
    average_book_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Author
        fields = ['id', 'name', 'bio', 'books_count', 'average_book_price']
        read_only_fields = ['id']


class AuthorNestedSerializer(serializers.ModelSerializer):
    """Light serializer for displaying author inside book."""

    class Meta:
        model = Author
        fields = ['id', 'name']


class BookSerializer(serializers.ModelSerializer):
    """Serializer for Book model."""

    cover = serializers.ImageField(use_url=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 
            'description', 'price', 'stock', 
            'cover', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['author'] = AuthorNestedSerializer(instance.author).data
        return representation


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model."""

    class Meta:
        model = OrderItem
        fields = ['id', 'book', 'quantity', 'price']
        read_only_fields = ['id', 'price']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""

    order_items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'total_price', 'created_at', 'order_items']
        read_only_fields = ['id', 'created_at', 'total_price', 'user']


class CheckoutItemSerializer(serializers.Serializer):
    book = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CheckoutOrderSerializer(serializers.Serializer):
    items = CheckoutItemSerializer(many=True)