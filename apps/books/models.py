from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class Author(models.Model):
    """Represents a book author."""

    name = models.CharField(max_length=255, unique=True, db_index=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Автори'


class Book(models.Model):
    """Represents a book available in the store."""

    title = models.CharField(max_length=255, db_index=True)
    author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name='books')
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    stock = models.PositiveIntegerField(default=0)
    cover = models.ImageField(upload_to='book_covers/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
    

class Order(models.Model):
    """Represents a customer order."""

    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        PAID = 'PAID', 'Paid'
        CANCELED = 'CANCELED', 'Canceled'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Замовлення #{self.id} від {self.user.username}'

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'
    

class OrderItem(models.Model):
    """Represents a single book line within an order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def calculate_total_price(self):
        """Return total price for this line item (price × quantity)."""
        return self.price * self.quantity

    def __str__(self):
        return f'{self.book.title} x{self.quantity}'

    class Meta:
        verbose_name = 'Товар у замовленні'
        verbose_name_plural = 'Товари у замовленні'
