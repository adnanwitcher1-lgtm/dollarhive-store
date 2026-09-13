from django.contrib import admin
from .models import Category, Product, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount_price', 'stock', 'is_featured')
    list_filter = ('category', 'is_featured')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'line_total')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer_name', 'customer_email', 'order_total',
        'status', 'is_paid', 'created_at',
    )
    list_filter = ('status', 'is_paid', 'created_at')
    search_fields = ('customer_name', 'customer_email', 'customer_phone')
    inlines = [OrderItemInline]
    readonly_fields = ('order_total', 'customer_notified', 'merchant_notified')
