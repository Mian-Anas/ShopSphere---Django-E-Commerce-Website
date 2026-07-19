"""
Tests for the Orders app — Order model, utils calculations, invoice.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from apps.store.models import Category, Product, Coupon
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem, generate_order_number
from apps.orders.utils import calculate_order_totals
from django.utils import timezone
from datetime import timedelta


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='orderuser', password='TestPass123!')

    def test_order_number_unique(self):
        n1 = generate_order_number()
        n2 = generate_order_number()
        self.assertNotEqual(n1, n2)
        self.assertTrue(n1.startswith('ORD-'))

    def test_order_creation(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal('99.99'))
        self.assertTrue(order.order_number.startswith('ORD-'))
        self.assertEqual(order.status, 'pending')

    def test_order_item_total(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal('50.00'))
        cat = Category.objects.create(name='TestCat')
        product = Product.objects.create(name='Item', category=cat, price=Decimal('25.00'), stock=10)
        item = OrderItem.objects.create(
            order=order, product=product, product_name='Item',
            price=Decimal('25.00'), quantity=2,
        )
        self.assertEqual(item.get_total_price(), Decimal('50.00'))


class OrderTotalsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='totalsuser', password='TestPass123!')
        self.cat = Category.objects.create(name='Test')
        self.product = Product.objects.create(
            name='Product', category=self.cat,
            price=Decimal('50.00'), stock=20,
        )
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_totals_without_coupon(self):
        totals = calculate_order_totals(self.cart)
        self.assertEqual(totals['subtotal'], Decimal('100.00'))
        # $100 => free shipping
        self.assertEqual(totals['shipping_cost'], Decimal('0'))
        # Tax = 10% of (100 - 0) = 10
        self.assertEqual(totals['tax_amount'], Decimal('10.00'))
        self.assertEqual(totals['total'], Decimal('110.00'))

    def test_totals_with_shipping(self):
        # Reduce qty so subtotal < $100
        CartItem.objects.filter(cart=self.cart).update(quantity=1)
        totals = calculate_order_totals(self.cart)
        self.assertEqual(totals['subtotal'], Decimal('50.00'))
        self.assertEqual(totals['shipping_cost'], Decimal('5.00'))

    def test_totals_with_percentage_coupon(self):
        coupon = Coupon.objects.create(
            code='SAVE10',
            discount_type='percentage',
            discount_value=Decimal('10'),
            active_from=timezone.now() - timedelta(hours=1),
            active_to=timezone.now() + timedelta(days=1),
            is_active=True,
        )
        totals = calculate_order_totals(self.cart, coupon)
        self.assertEqual(totals['discount_amount'], Decimal('10.00'))  # 10% of 100
