"""
Orders Views — Checkout, Stripe session, Success, Cancel, Order detail, Invoice PDF.
"""
import json
import stripe
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET

from apps.cart.views import get_or_create_cart
from apps.store.models import Coupon
from apps.accounts.models import Address
from .models import Order, OrderItem
from .utils import generate_invoice_pdf, calculate_order_totals

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def checkout_view(request):
    cart = get_or_create_cart(request)

    if cart.is_empty():
        messages.warning(request, 'Your cart is empty. Add some items before checking out.')
        return redirect('cart:cart')

    addresses = request.user.addresses.all()
    coupon = None
    coupon_error = None

    # Handle coupon application
    coupon_code = request.session.get('coupon_code', '')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code.upper())
            valid, msg = coupon.is_valid()
            if not valid:
                coupon = None
                coupon_error = msg
                del request.session['coupon_code']
        except Coupon.DoesNotExist:
            coupon = None
            del request.session['coupon_code']

    totals = calculate_order_totals(cart, coupon)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        # Apply coupon
        if action == 'apply_coupon':
            entered_code = request.POST.get('coupon_code', '').strip().upper()
            try:
                c = Coupon.objects.get(code=entered_code)
                valid, msg = c.is_valid()
                if valid:
                    if totals['subtotal'] >= c.minimum_amount:
                        request.session['coupon_code'] = entered_code
                        messages.success(request, f'Coupon "{entered_code}" applied!')
                    else:
                        messages.error(request, f'Minimum order amount is ${c.minimum_amount} for this coupon.')
                else:
                    messages.error(request, msg)
            except Coupon.DoesNotExist:
                messages.error(request, 'Invalid coupon code.')
            return redirect('orders:checkout')

        # Remove coupon
        if action == 'remove_coupon':
            if 'coupon_code' in request.session:
                del request.session['coupon_code']
            messages.info(request, 'Coupon removed.')
            return redirect('orders:checkout')

        # Place order and redirect to Stripe
        if action == 'place_order':
            shipping_address_id = request.POST.get('shipping_address')
            billing_address_id = request.POST.get('billing_address')

            if not shipping_address_id or not billing_address_id:
                messages.error(request, 'Please select both shipping and billing addresses.')
                return redirect('orders:checkout')

            shipping_address = get_object_or_404(Address, pk=shipping_address_id, user=request.user)
            billing_address = get_object_or_404(Address, pk=billing_address_id, user=request.user)

            # Create order
            order = Order(user=request.user)
            order.copy_from_address(shipping_address, 'shipping')
            order.copy_from_address(billing_address, 'billing')
            order.subtotal = totals['subtotal']
            order.shipping_cost = totals['shipping_cost']
            order.tax_amount = totals['tax_amount']
            order.discount_amount = totals['discount_amount']
            order.total_amount = totals['total']
            if coupon:
                order.coupon_code = coupon.code
            order.save()

            # Create order items
            cart_items = cart.items.select_related('product').all()
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    product_sku=cart_item.product.sku,
                    price=cart_item.product.get_effective_price(),
                    quantity=cart_item.quantity,
                )

            # Create Stripe Checkout Session
            try:
                line_items = []
                for cart_item in cart_items:
                    line_items.append({
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': cart_item.product.name,
                                'description': cart_item.product.description[:100] if cart_item.product.description else '',
                            },
                            'unit_amount': int(cart_item.product.get_effective_price() * 100),
                        },
                        'quantity': cart_item.quantity,
                    })

                # Add shipping as a line item if applicable
                if totals['shipping_cost'] > 0:
                    line_items.append({
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {'name': 'Shipping'},
                            'unit_amount': int(totals['shipping_cost'] * 100),
                        },
                        'quantity': 1,
                    })

                # Add tax
                if totals['tax_amount'] > 0:
                    line_items.append({
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {'name': 'Tax (10%)'},
                            'unit_amount': int(totals['tax_amount'] * 100),
                        },
                        'quantity': 1,
                    })

                # Apply discount
                discounts = []
                if totals['discount_amount'] > 0:
                    stripe_coupon = stripe.Coupon.create(
                        amount_off=int(totals['discount_amount'] * 100),
                        currency='usd',
                        duration='once',
                        name=f'Discount ({coupon.code})',
                    )
                    discounts = [{'coupon': stripe_coupon.id}]

                success_url = request.build_absolute_uri(
                    reverse('orders:success') + f'?order={order.order_number}'
                )
                cancel_url = request.build_absolute_uri(
                    reverse('orders:cancel') + f'?order={order.order_number}'
                )

                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=line_items,
                    mode='payment',
                    success_url=success_url,
                    cancel_url=cancel_url,
                    customer_email=request.user.email,
                    discounts=discounts if discounts else [],
                    metadata={'order_number': order.order_number},
                )

                order.stripe_session_id = checkout_session.id
                order.save(update_fields=['stripe_session_id'])

                # Clear coupon from session
                if 'coupon_code' in request.session:
                    del request.session['coupon_code']

                return redirect(checkout_session.url)

            except stripe.error.StripeError as e:
                order.delete()
                messages.error(request, f'Payment error: {str(e)}')
                return redirect('orders:checkout')

    context = {
        'cart': cart,
        'cart_items': cart.items.select_related('product').prefetch_related('product__images').all(),
        'addresses': addresses,
        'coupon': coupon,
        'coupon_error': coupon_error,
        'totals': totals,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_success_view(request):
    order_number = request.GET.get('order', '')
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/success.html', {'order': order})


@login_required
def order_cancel_view(request):
    order_number = request.GET.get('order', '')
    order = None
    if order_number:
        try:
            order = Order.objects.get(order_number=order_number, user=request.user)
        except Order.DoesNotExist:
            pass
    return render(request, 'orders/cancel.html', {'order': order})


@login_required
def order_list_view(request):
    orders = request.user.orders.prefetch_related('items').order_by('-created_at')
    return render(request, 'orders/orders.html', {'orders': orders})


@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        order_number=order_number,
        user=request.user
    )
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def download_invoice_view(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related('items'),
        order_number=order_number,
        user=request.user
    )
    return generate_invoice_pdf(order)


@login_required
@require_POST
def apply_coupon_ajax(request):
    """AJAX endpoint to validate coupon and return discount info."""
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip().upper()
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

    try:
        coupon = Coupon.objects.get(code=code)
        valid, msg = coupon.is_valid()
        if not valid:
            return JsonResponse({'success': False, 'message': msg})

        cart = get_or_create_cart(request)
        subtotal = float(cart.get_subtotal())

        if subtotal < float(coupon.minimum_amount):
            return JsonResponse({
                'success': False,
                'message': f'Minimum order amount for this coupon is ${coupon.minimum_amount}.'
            })

        discount = float(coupon.calculate_discount(cart.get_subtotal()))
        request.session['coupon_code'] = code

        return JsonResponse({
            'success': True,
            'message': f'Coupon "{code}" applied! You save ${discount:.2f}.',
            'discount': discount,
            'coupon_code': code,
        })

    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon code.'})
