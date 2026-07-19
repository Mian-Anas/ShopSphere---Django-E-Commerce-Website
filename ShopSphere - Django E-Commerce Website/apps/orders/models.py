"""
Orders Models — Order, OrderItem.
"""
from django.db import models
from django.contrib.auth.models import User
from apps.store.models import Product
from apps.accounts.models import Address
import uuid


def generate_order_number():
    return f'ORD-{uuid.uuid4().hex[:10].upper()}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders')
    order_number = models.CharField(max_length=30, unique=True, default=generate_order_number)

    # Snapshot addresses (not FK, so deletions don't affect history)
    shipping_full_name = models.CharField(max_length=150, blank=True)
    shipping_address_line1 = models.CharField(max_length=255, blank=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)

    billing_full_name = models.CharField(max_length=150, blank=True)
    billing_address_line1 = models.CharField(max_length=255, blank=True)
    billing_address_line2 = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=100, blank=True)

    # Financials
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    coupon_code = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    # Stripe
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    stripe_session_id = models.CharField(max_length=200, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'Order {self.order_number}'

    def get_status_display_class(self):
        classes = {
            'pending': 'warning',
            'paid': 'info',
            'processing': 'primary',
            'shipped': 'primary',
            'delivered': 'success',
            'cancelled': 'danger',
            'refunded': 'secondary',
        }
        return classes.get(self.status, 'secondary')

    def get_progress_step(self):
        steps = {
            'pending': 1,
            'paid': 2,
            'processing': 2,
            'shipped': 3,
            'delivered': 4,
            'cancelled': 0,
            'refunded': 0,
        }
        return steps.get(self.status, 1)

    def get_shipping_address(self):
        parts = [self.shipping_address_line1]
        if self.shipping_address_line2:
            parts.append(self.shipping_address_line2)
        parts.extend([self.shipping_city, self.shipping_state, self.shipping_postal_code, self.shipping_country])
        return ', '.join(filter(None, parts))

    def copy_from_address(self, address: Address, address_type: str = 'shipping'):
        prefix = address_type
        setattr(self, f'{prefix}_full_name', address.full_name)
        setattr(self, f'{prefix}_address_line1', address.address_line1)
        setattr(self, f'{prefix}_address_line2', address.address_line2)
        setattr(self, f'{prefix}_city', address.city)
        setattr(self, f'{prefix}_state', address.state)
        setattr(self, f'{prefix}_postal_code', address.postal_code)
        setattr(self, f'{prefix}_country', address.country)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, related_name='order_items'
    )
    product_name = models.CharField(max_length=300)  # snapshot
    product_sku = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f'{self.quantity}x {self.product_name} — {self.order.order_number}'

    def get_total_price(self):
        if self.price is None:
            return 0
        return self.price * self.quantity
