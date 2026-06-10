from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.books.models import Author, Book, Order, OrderItem

User = get_user_model()


class BookApiTests(APITestCase):
    def setUp(self):
        self.regular_user = User.objects.create_user(
            username='book_client', 
            email='client@gmail.com', 
            password='password123'
        )
        self.admin_user = User.objects.create_superuser(
            username='book_admin', 
            email='admin@gmail.com', 
            password='password123'
        )
        self.author = Author.objects.create(name='Martin Fowler')
        self.book = Book.objects.create(
            title='Refactoring',
            author=self.author,
            price=600.00,
            stock=10
        )
        self.detail_url = reverse('books-detail', kwargs={'pk': self.book.id})

    def test_regular_user_cannot_update_book(self):
        self.client.force_authenticate(user=self.regular_user)
        payload = {'title': 'Hacked Title', 'price': 1.00}
        response = self.client.patch(self.detail_url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, 'Refactoring')

    def test_admin_user_can_update_book(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {'price': 750.00}
        response = self.client.patch(self.detail_url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.price, 750.00)


class OrderCheckoutApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='checkout_client', 
            email='checkout_client@gmail.com', 
            password='password123'
        )
        self.author = Author.objects.create(name='Martin Fowler')
        self.book = Book.objects.create(
            title='Refactoring', author=self.author, price=600.00, stock=10
        )
        self.out_of_stock_book = Book.objects.create(
            title='Sold Out Book', author=self.author, price=300.00, stock=0
        )
        self.url = reverse('orders-checkout')

    def test_checkout_success(self):
        self.client.force_authenticate(user=self.user)
        items = {
            "items": [
                {'book': self.book.id, 'quantity': 2}
            ]
        }
        response = self.client.post(self.url, items, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.stock, 8)
        self.assertTrue(Order.objects.filter(user=self.user).exists())

    def test_checkout_failed_if_stock_is_zero(self):
        self.client.force_authenticate(user=self.user)
        items = {
            "items": [
                {'book': self.out_of_stock_book.id, 'quantity': 1}
            ]
        }
        response = self.client.post(self.url, items, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Order.objects.filter(user=self.user).exists())


class OrderTransactionApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tx_client', email='tx_client@gmail.com', password='password123'
        )
        self.author = Author.objects.create(name='Clean Code Author')
        self.book_available = Book.objects.create(
            title='Book A', author=self.author, price=100.00, stock=1
        )
        self.book_out_of_stock = Book.objects.create(
            title='Book B', author=self.author, price=200.00, stock=0
        )
        self.url = reverse('orders-checkout')

    def test_checkout_transaction_rolls_back_on_error(self):
        self.client.force_authenticate(user=self.user)
        items = {
            "items": [
                {"book": self.book_available.id, "quantity": 1},
                {"book": self.book_out_of_stock.id, "quantity": 1}
            ]
        }
        response = self.client.post(self.url, items, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.book_available.refresh_from_db()
        self.assertEqual(self.book_available.stock, 1)
        self.assertFalse(Order.objects.filter(user=self.user).exists())


class OrderIsolationApiTests(APITestCase):
    def setUp(self):
        self.user_alex = User.objects.create_user(
            username='alex', email='alex@gmail.com', password='password123'
        )
        self.user_bob = User.objects.create_user(
            username='bob', email='bob@gmail.com', password='password123'
        )
        self.alex_order = Order.objects.create(user=self.user_alex, total_price=500.00)
        
        self.detail_url = f'/api/v1/orders/{self.alex_order.id}/'

    def test_user_cannot_view_others_order(self):
        self.client.force_authenticate(user=self.user_bob)
        response = self.client.get(self.detail_url)

        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_user_can_view_own_order(self):
        self.client.force_authenticate(user=self.user_alex)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)