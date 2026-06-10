from django.contrib import admin
from .models import Book, Author, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price', 'quantity', 'book')


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'price', 'stock')
    list_filter = ('author',)
    search_fields = ('title', 'author__name')
    list_editable = ('price', 'stock')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'id')
    readonly_fields = ('total_price', 'created_at')
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False