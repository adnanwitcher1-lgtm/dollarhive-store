"""
DollarHive store models.

Category   -> product categories shown in "Shop by Category" and the
              "All Categories" dropdown.
Product    -> individual sellable items shown in the product grid.
Order      -> a placed customer order (checkout record).
OrderItem  -> a single product line inside an Order.
"""
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator


class Category(models.Model):
    """A product category, e.g. Electronics, Laptops, Audio, Home."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-generate the slug from the name if one wasn't supplied.
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:products') + f'?category={self.slug}'


class Product(models.Model):
    """A single product available for purchase on DollarHive."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products'
    )
    description = models.TextField(blank=True)

    # `price` is the current selling price. `discount_price`, if set and
    # lower than `price`, is shown struck-through as the "was" price so
    # the product card can display a savings badge.
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        validators=[MinValueValidator(0)],
        help_text='Original / "was" price. Leave blank if not discounted.'
    )

    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    stock = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=4.5,
        help_text='Average star rating out of 5.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        # Auto-correct: `discount_price` must always be the HIGHER
        # ("was") price and `price` the LOWER ("now") price for the
        # frontend badge/strikethrough to show. If someone enters
        # discount_price as a smaller sale price by mistake, swap the
        # two so it still displays correctly — no frontend change needed.
        if self.discount_price is not None and self.discount_price < self.price:
            self.price, self.discount_price = self.discount_price, self.price

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_detail', kwargs={'slug': self.slug})

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def discount_percent(self):
        """Whole-number % off, used for the yellow savings badge."""
        if self.discount_price and self.discount_price > self.price:
            return round(
                (self.discount_price - self.price) / self.discount_price * 100
            )
        return 0


class Order(models.Model):
    """A placed customer order, created at checkout."""

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Payment'),
        (STATUS_PAID, 'Paid'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    customer_phone = models.CharField(
        max_length=20,
        help_text='Include country code, e.g. +923001234567, for WhatsApp receipts.'
    )

    shipping_address = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)

    order_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    is_paid = models.BooleanField(default=False)

    # Set once the confirmation notifications have successfully fired,
    # so checkout doesn't re-send duplicate emails/WhatsApp messages.
    customer_notified = models.BooleanField(default=False)
    merchant_notified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.pk} — {self.customer_name}'

    def recalculate_total(self):
        total = sum(item.line_total for item in self.items.all())
        self.order_total = total
        self.save(update_fields=['order_total'])
        return total


class OrderItem(models.Model):
    """A single product line within an Order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, related_name='order_items'
    )
    product_name = models.CharField(
        max_length=200,
        help_text='Snapshot of the product name at time of purchase.'
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Snapshot of the unit price at time of purchase.'
    )
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'

    @property
    def line_total(self):
        if self.price is None or self.quantity is None:
            return 0
        return self.price * self.quantity
