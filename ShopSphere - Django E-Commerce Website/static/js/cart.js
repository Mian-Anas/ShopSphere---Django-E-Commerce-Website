/**
 * ShopSphere — Cart & Wishlist JavaScript
 * AJAX add/update/remove cart items + wishlist toggle
 */

'use strict';

// ── Add to Cart ───────────────────────────────────────────────────────────────
function initAddToCart() {
  document.querySelectorAll('[data-add-to-cart]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const productId = btn.dataset.productId;
      const qtyInput = document.querySelector(`#qty-input-${productId}`) || document.querySelector('[name="quantity"]');
      const quantity = qtyInput ? parseInt(qtyInput.value) : 1;

      const originalHtml = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-glow"></span> Adding...';

      try {
        const resp = await csrfFetch('/cart/add/', {
          method: 'POST',
          body: JSON.stringify({ product_id: productId, quantity }),
        });
        const data = await resp.json();

        if (data.success) {
          Toast.success(data.message);
          updateCartCount(data.cart_count);
          // Animate cart icon
          const cartIcon = document.querySelector('.nav-icon-btn[data-cart]');
          if (cartIcon) {
            cartIcon.classList.add('pulse-glow');
            setTimeout(() => cartIcon.classList.remove('pulse-glow'), 600);
          }
        } else {
          Toast.error(data.message);
        }
      } catch {
        Toast.error('Failed to add item. Please try again.');
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
      }
    });
  });
}

// ── Update Cart Item Quantity ─────────────────────────────────────────────────
function initCartQuantityUpdate() {
  document.querySelectorAll('[data-cart-item-id]').forEach(wrapper => {
    const itemId = wrapper.dataset.cartItemId;
    const qtyInput = wrapper.querySelector('.qty-input');
    if (!qtyInput) return;

    let debounceTimer;
    qtyInput.addEventListener('change', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => updateCartItem(itemId, parseInt(qtyInput.value)), 500);
    });
  });
}

async function updateCartItem(itemId, quantity) {
  try {
    const resp = await csrfFetch('/cart/update/', {
      method: 'POST',
      body: JSON.stringify({ item_id: itemId, quantity }),
    });
    const data = await resp.json();

    if (data.success) {
      if (data.removed) {
        // Remove row from DOM
        const row = document.querySelector(`[data-cart-item-row="${itemId}"]`);
        if (row) {
          row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
          row.style.opacity = '0';
          row.style.transform = 'translateX(-20px)';
          setTimeout(() => { row.remove(); refreshCartTotals(data); }, 300);
        }
        Toast.info(data.message);
      } else {
        // Update item total
        const itemTotal = document.querySelector(`[data-item-total="${itemId}"]`);
        if (itemTotal) itemTotal.textContent = `$${data.item_total}`;
        refreshCartTotals(data);
        Toast.success(data.message);
      }
    } else {
      Toast.error(data.message);
    }
  } catch {
    Toast.error('Failed to update cart.');
  }
}

// ── Remove Cart Item ──────────────────────────────────────────────────────────
function initRemoveCartItem() {
  document.querySelectorAll('[data-remove-item]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const itemId = btn.dataset.removeItem;

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-glow"></span>';

      try {
        const resp = await csrfFetch('/cart/remove/', {
          method: 'POST',
          body: JSON.stringify({ item_id: itemId }),
        });
        const data = await resp.json();

        if (data.success) {
          const row = document.querySelector(`[data-cart-item-row="${itemId}"]`);
          if (row) {
            row.style.transition = 'all 0.35s ease';
            row.style.opacity = '0';
            row.style.transform = 'scale(0.95)';
            setTimeout(() => {
              row.remove();
              refreshCartTotals(data);
              checkEmptyCart();
            }, 350);
          }
          Toast.info(data.message);
        } else {
          Toast.error(data.message);
          btn.disabled = false;
        }
      } catch {
        Toast.error('Failed to remove item.');
        btn.disabled = false;
      }
    });
  });
}

function refreshCartTotals(data) {
  updateCartCount(data.cart_count);
  const subtotalEls = document.querySelectorAll('.cart-subtotal-display');
  subtotalEls.forEach(el => { el.textContent = `$${data.cart_subtotal}`; });
}

function checkEmptyCart() {
  const rows = document.querySelectorAll('[data-cart-item-row]');
  if (rows.length === 0) {
    const table = document.getElementById('cartTable');
    const emptyState = document.getElementById('cartEmpty');
    const sidebar = document.getElementById('cartSidebar');
    if (table) table.style.display = 'none';
    if (sidebar) sidebar.style.display = 'none';
    if (emptyState) emptyState.style.display = 'block';
  }
}

// ── Wishlist Toggle ───────────────────────────────────────────────────────────
function initWishlistToggle() {
  document.querySelectorAll('[data-toggle-wishlist]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();

      // Redirect to login if not authenticated
      if (btn.dataset.requiresAuth === 'true') {
        Toast.info('Please log in to add items to your wishlist.');
        setTimeout(() => { window.location.href = '/accounts/login/?next=' + window.location.pathname; }, 800);
        return;
      }

      const productId = btn.dataset.productId;
      const originalHtml = btn.innerHTML;
      btn.disabled = true;

      try {
        const resp = await csrfFetch('/cart/wishlist/toggle/', {
          method: 'POST',
          body: JSON.stringify({ product_id: productId }),
        });
        const data = await resp.json();

        if (data.success) {
          if (data.in_wishlist) {
            btn.classList.add('wishlisted');
            btn.title = 'Remove from wishlist';
            btn.innerHTML = '♥';
            Toast.success(data.message);
          } else {
            btn.classList.remove('wishlisted');
            btn.title = 'Add to wishlist';
            btn.innerHTML = '♡';
            Toast.info(data.message);
          }
        } else {
          Toast.error(data.message);
          btn.innerHTML = originalHtml;
        }
      } catch {
        Toast.error('Failed to update wishlist.');
        btn.innerHTML = originalHtml;
      } finally {
        btn.disabled = false;
      }
    });
  });
}

// ── Qty Steppers on Cart Page ────────────────────────────────────────────────
function initCartQtySteppers() {
  document.querySelectorAll('[data-cart-item-id]').forEach(wrapper => {
    const itemId = wrapper.dataset.cartItemId;
    const minusBtn = wrapper.querySelector('[data-qty-minus]');
    const plusBtn = wrapper.querySelector('[data-qty-plus]');
    const qtyInput = wrapper.querySelector('.qty-input');
    if (!qtyInput) return;

    if (minusBtn) {
      minusBtn.addEventListener('click', () => {
        const newQty = Math.max(0, parseInt(qtyInput.value) - 1);
        qtyInput.value = newQty;
        updateCartItem(itemId, newQty);
      });
    }

    if (plusBtn) {
      plusBtn.addEventListener('click', () => {
        const max = parseInt(qtyInput.max) || 999;
        const newQty = Math.min(max, parseInt(qtyInput.value) + 1);
        qtyInput.value = newQty;
        updateCartItem(itemId, newQty);
      });
    }
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initAddToCart();
  initRemoveCartItem();
  initCartQuantityUpdate();
  initCartQtySteppers();
  initWishlistToggle();
});
