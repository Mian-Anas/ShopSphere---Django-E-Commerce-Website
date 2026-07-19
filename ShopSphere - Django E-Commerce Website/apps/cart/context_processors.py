"""
Cart Context Processor — expose cart data globally to all templates.
"""
from .models import Cart, CartItem


def cart_context(request):
    cart = None
    cart_items = []
    cart_count = 0
    cart_subtotal = 0

    if request.user.is_authenticated:
        try:
            cart = Cart.objects.prefetch_related('items__product__images').get(user=request.user)
            cart_items = cart.items.select_related('product').prefetch_related('product__images').all()
            cart_count = cart.get_total_items()
            cart_subtotal = cart.get_subtotal()
        except Cart.DoesNotExist:
            pass
    else:
        session_id = request.session.session_key
        if session_id:
            try:
                cart = Cart.objects.prefetch_related('items__product').get(session_id=session_id)
                cart_items = cart.items.select_related('product').all()
                cart_count = cart.get_total_items()
                cart_subtotal = cart.get_subtotal()
            except Cart.DoesNotExist:
                pass

    return {
        'cart': cart,
        'cart_items': cart_items,
        'cart_count': cart_count,
        'cart_subtotal': cart_subtotal,
    }
