"""
Tests for the Cart app — Cart creation, item add/update/remove, AJAX endpoints.
"""
import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.store.models import Category, Product
from apps.cart.models import Cart, CartItem, Wishlist
from apps.cart.views import get_or_create_cart


class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cartuser', password='TestPass123!')
        self.cat = Category.objects.create(name='Cat')
        self.product = Product.objects.create(
            name='Widget', category=self.cat,
            price=Decimal('10.00'), stock=20,
        )

    def test_cart_created_for_user(self):
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(str(cart), "cartuser's Cart")

    def test_cart_item_total(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=3)
        self.assertEqual(item.get_total_price(), Decimal('30.00'))

    def test_cart_subtotal(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.assertEqual(cart.get_subtotal(), Decimal('20.00'))

    def test_cart_total_items(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=5)
        self.assertEqual(cart.get_total_items(), 5)


class CartAJAXViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='ajaxuser', password='TestPass123!')
        self.client.login(username='ajaxuser', password='TestPass123!')
        self.cat = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Phone', category=self.cat,
            price=Decimal('299.00'), stock=10,
        )

    def _post_json(self, url, data):
        return self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

    def test_add_to_cart(self):
        resp = self._post_json(reverse('cart:add'), {'product_id': self.product.pk, 'quantity': 1})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 1)

    def test_add_to_cart_out_of_stock(self):
        self.product.stock = 0
        self.product.save()
        resp = self._post_json(reverse('cart:add'), {'product_id': self.product.pk, 'quantity': 1})
        data = resp.json()
        self.assertFalse(data['success'])

    def test_update_cart_item(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        resp = self._post_json(reverse('cart:update'), {'item_id': item.pk, 'quantity': 3})
        data = resp.json()
        self.assertTrue(data['success'])
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

    def test_remove_cart_item(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        resp = self._post_json(reverse('cart:remove'), {'item_id': item.pk})
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_wishlist_toggle_add(self):
        resp = self._post_json(reverse('cart:toggle_wishlist'), {'product_id': self.product.pk})
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['in_wishlist'])
        self.assertTrue(Wishlist.objects.filter(user=self.user, product=self.product).exists())

    def test_wishlist_toggle_remove(self):
        Wishlist.objects.create(user=self.user, product=self.product)
        resp = self._post_json(reverse('cart:toggle_wishlist'), {'product_id': self.product.pk})
        data = resp.json()
        self.assertFalse(data['in_wishlist'])
        self.assertFalse(Wishlist.objects.filter(user=self.user, product=self.product).exists())
