from datetime import timedelta
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction

from apps.books.models import Order, OrderItem, Book


@shared_task
def send_order_confirmation_email(order_id):
    """Send order confirmation email to the customer after successful checkout."""
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return

    items = OrderItem.objects.filter(order=order).select_related('book')

    items_text = '\n'.join([
        f'  📖 {item.book.title} x{item.quantity} — {item.price} грн'
        for item in items
    ])

    message = render_to_string('email/order_confirmation.txt', {
        'username': order.user.username,
        'order_id': order.id,
        'items_text': items_text,
        'total_price': order.total_price,
    })

    send_mail(
        subject=f'✅ Замовлення #{order.id} підтверджено — Book Store Pro',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
    )


@shared_task
def cancel_unpaid_orders():
    """Cancel unpaid orders older than 24 hours and restore book stock."""

    cutoff_time = timezone.now() - timedelta(hours=24)
    orders = Order.objects.filter(created_at__lte=cutoff_time, status=Order.Status.NEW)

    for order in orders:
        with transaction.atomic():
            items = OrderItem.objects.filter(order=order).select_related('book')

            for item in items:
                book = Book.objects.select_for_update().get(id=item.book.id)
                book.stock += item.quantity
                book.save()

            order.status = Order.Status.CANCELED
            order.save()