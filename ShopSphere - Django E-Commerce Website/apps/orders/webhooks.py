"""
Stripe Webhook Handler — verify signatures, mark orders paid, deduct stock, clear cart.
"""
import json
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Order


@csrf_exempt
@require_POST
def stripe_webhook_view(request):
    """
    Handle Stripe webhook events securely by verifying the signature.
    Processes: checkout.session.completed
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        _handle_checkout_session_completed(session)

    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        _handle_payment_failed(payment_intent)

    return HttpResponse(status=200)


def _handle_checkout_session_completed(session):
    """Mark order as paid, deduct stock, clear cart."""
    session_id = session.get('id', '')
    payment_intent_id = session.get('payment_intent', '')

    try:
        order = Order.objects.get(stripe_session_id=session_id)
    except Order.DoesNotExist:
        return

    if order.status != 'pending':
        return  # Already processed

    # Mark paid
    order.status = 'paid'
    order.stripe_payment_intent_id = payment_intent_id
    order.save()

    # Deduct stock for each order item
    for item in order.items.select_related('product').all():
        if item.product:
            item.product.stock = max(0, item.product.stock - item.quantity)
            item.product.save(update_fields=['stock'])

    # Clear the user's cart
    if order.user:
        try:
            cart = order.user.cart
            cart.items.all().delete()
        except Exception:
            pass

    # Increment coupon usage if applicable
    if order.coupon_code:
        from apps.store.models import Coupon
        try:
            coupon = Coupon.objects.get(code=order.coupon_code)
            coupon.used_count += 1
            coupon.save(update_fields=['used_count'])
        except Coupon.DoesNotExist:
            pass


def _handle_payment_failed(payment_intent):
    """Handle failed payments — optionally notify the user."""
    payment_intent_id = payment_intent.get('id', '')
    try:
        order = Order.objects.get(stripe_payment_intent_id=payment_intent_id)
        order.status = 'pending'
        order.save(update_fields=['status'])
    except Order.DoesNotExist:
        pass
