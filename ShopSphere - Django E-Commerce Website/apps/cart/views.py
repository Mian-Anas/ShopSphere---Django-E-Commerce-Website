"""
Cart Views — AJAX add/update/remove cart, wishlist toggle, cart display.
"""
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from apps.store.models import Product
from .models import Cart, CartItem, Wishlist


# ─── Cart Helpers ─────────────────────────────────────────────────────────────

def get_or_create_cart(request):
    """Get or create cart for authenticated user or guest session."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_id=session_id, user=None)
    return cart


# ─── Cart AJAX Views ───────────────────────────────────────────────────────────

@require_POST
def add_to_cart_view(request):
    try:
        data = json.loads(request.body)
        product_id = int(data.get('product_id', 0))
        quantity = int(data.get('quantity', 1))
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'message': 'Invalid request data.'}, status=400)

    product = get_object_or_404(Product, pk=product_id, is_active=True)

    if not product.is_in_stock():
        return JsonResponse({'success': False, 'message': 'This product is out of stock.'}, status=400)

    if quantity < 1:
        return JsonResponse({'success': False, 'message': 'Quantity must be at least 1.'}, status=400)

    if quantity > product.stock:
        return JsonResponse({
            'success': False,
            'message': f'Only {product.stock} units available.'
        }, status=400)

    cart = get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        new_qty = item.quantity + quantity
        if new_qty > product.stock:
            new_qty = product.stock
        item.quantity = new_qty
    else:
        item.quantity = quantity
    item.save()

    return JsonResponse({
        'success': True,
        'message': f'"{product.name}" added to cart.',
        'cart_count': cart.get_total_items(),
        'cart_subtotal': str(cart.get_subtotal()),
    })


@require_POST
def update_cart_view(request):
    try:
        data = json.loads(request.body)
        item_id = int(data.get('item_id', 0))
        quantity = int(data.get('quantity', 1))
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'message': 'Invalid data.'}, status=400)

    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)

    if quantity < 1:
        item.delete()
        return JsonResponse({
            'success': True,
            'removed': True,
            'message': 'Item removed from cart.',
            'cart_count': cart.get_total_items(),
            'cart_subtotal': str(cart.get_subtotal()),
        })

    if quantity > item.product.stock:
        quantity = item.product.stock

    item.quantity = quantity
    item.save()

    return JsonResponse({
        'success': True,
        'message': 'Cart updated.',
        'item_total': str(item.get_total_price()),
        'cart_count': cart.get_total_items(),
        'cart_subtotal': str(cart.get_subtotal()),
    })


@require_POST
def remove_from_cart_view(request):
    try:
        data = json.loads(request.body)
        item_id = int(data.get('item_id', 0))
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'message': 'Invalid data.'}, status=400)

    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    product_name = item.product.name
    item.delete()

    return JsonResponse({
        'success': True,
        'message': f'"{product_name}" removed from cart.',
        'cart_count': cart.get_total_items(),
        'cart_subtotal': str(cart.get_subtotal()),
    })


def cart_detail_view(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product').prefetch_related('product__images').all()
    return render(request, 'cart/cart.html', {
        'cart': cart,
        'items': items,
    })


# ─── Wishlist Views ────────────────────────────────────────────────────────────

@login_required
@require_POST
def toggle_wishlist_view(request):
    try:
        data = json.loads(request.body)
        product_id = int(data.get('product_id', 0))
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'message': 'Invalid data.'}, status=400)

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

    if not created:
        wishlist_item.delete()
        return JsonResponse({
            'success': True,
            'in_wishlist': False,
            'message': f'"{product.name}" removed from wishlist.',
        })

    return JsonResponse({
        'success': True,
        'in_wishlist': True,
        'message': f'"{product.name}" added to wishlist.',
    })


@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product').prefetch_related('product__images').order_by('-added_at')
    return render(request, 'cart/wishlist.html', {'wishlist_items': wishlist_items})


@login_required
@require_POST
def move_to_cart_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    Wishlist.objects.filter(user=request.user, product=product).delete()

    if product.is_in_stock():
        cart = get_or_create_cart(request)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += 1
            item.save()
        messages.success(request, f'"{product.name}" moved to cart.')
    else:
        messages.error(request, f'"{product.name}" is out of stock.')

    return redirect('cart:wishlist')
