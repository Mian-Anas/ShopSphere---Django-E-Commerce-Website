/**
 * ShopSphere — Main JavaScript
 * Live search autocomplete + Toast notifications + Utility functions
 */

'use strict';

// ── Toast Notification System ──────────────────────────────────────────────────
const Toast = (() => {
  let container = null;

  function getContainer() {
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      container.setAttribute('aria-live', 'polite');
      document.body.appendChild(container);
    }
    return container;
  }

  function show(message, type = 'info', duration = 3500) {
    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ',
    };

    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || icons.info}</span>
      <span class="toast-message">${message}</span>
      <button class="toast-close" aria-label="Dismiss">&times;</button>
    `;

    const c = getContainer();
    c.appendChild(toast);

    // Close button
    toast.querySelector('.toast-close').addEventListener('click', () => dismiss(toast));

    // Auto dismiss
    const timer = setTimeout(() => dismiss(toast), duration);
    toast._timer = timer;

    // Pause on hover
    toast.addEventListener('mouseenter', () => clearTimeout(toast._timer));
    toast.addEventListener('mouseleave', () => {
      toast._timer = setTimeout(() => dismiss(toast), 1500);
    });

    return toast;
  }

  function dismiss(toast) {
    if (!toast.parentNode) return;
    toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.parentNode && toast.parentNode.removeChild(toast), 350);
  }

  return { show, success: (m, d) => show(m, 'success', d), error: (m, d) => show(m, 'error', d), info: (m, d) => show(m, 'info', d), warning: (m, d) => show(m, 'warning', d) };
})();

window.Toast = Toast;

// ── CSRF Token Utility ────────────────────────────────────────────────────────
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function csrfFetch(url, options = {}) {
  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
      ...options.headers,
    },
  });
}

window.csrfFetch = csrfFetch;

// ── Live Search Autocomplete ──────────────────────────────────────────────────
function initLiveSearch() {
  const searchInput = document.getElementById('navbarSearchInput');
  const dropdown = document.getElementById('searchDropdown');
  if (!searchInput || !dropdown) return;

  let debounceTimer = null;
  const SEARCH_URL = searchInput.dataset.url || '/api/search/';
  const MIN_CHARS = 2;

  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim();
    clearTimeout(debounceTimer);

    if (q.length < MIN_CHARS) {
      hideDropdown();
      return;
    }

    debounceTimer = setTimeout(() => fetchResults(q), 280);
  });

  async function fetchResults(q) {
    try {
      const resp = await fetch(`${SEARCH_URL}?q=${encodeURIComponent(q)}`);
      if (!resp.ok) return;
      const data = await resp.json();
      renderResults(data.results);
    } catch (err) {
      console.warn('Search error:', err);
    }
  }

  function renderResults(results) {
    if (!results || results.length === 0) {
      dropdown.innerHTML = '<div class="search-result-item" style="justify-content:center;color:var(--text-muted);font-size:.85rem;">No results found</div>';
      showDropdown();
      return;
    }

    dropdown.innerHTML = results.map(r => `
      <a href="${r.url}" class="search-result-item" style="text-decoration:none;">
        ${r.image ? `<img src="${r.image}" class="search-result-img" alt="${r.name}">` : '<div class="search-result-img" style="background:var(--surface-3);display:flex;align-items:center;justify-content:center;font-size:1.2rem;">📦</div>'}
        <div class="search-result-info">
          <div class="search-result-name">${escapeHtml(r.name)}</div>
          <div class="search-result-price">$${r.price} ${r.category ? `· ${escapeHtml(r.category)}` : ''}</div>
        </div>
      </a>
    `).join('');
    showDropdown();
  }

  function showDropdown() { dropdown.classList.add('active'); }
  function hideDropdown() { dropdown.classList.remove('active'); }

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
      hideDropdown();
    }
  });

  // Keyboard navigation
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { hideDropdown(); searchInput.blur(); }
    if (e.key === 'Enter') {
      const q = searchInput.value.trim();
      if (q) {
        const shopUrl = searchInput.dataset.shopUrl || '/shop/';
        window.location.href = `${shopUrl}?q=${encodeURIComponent(q)}`;
      }
    }
  });
}

// ── Cart Count Updater ────────────────────────────────────────────────────────
function updateCartCount(count) {
  const badges = document.querySelectorAll('.cart-count-badge');
  badges.forEach(b => {
    b.textContent = count;
    b.style.display = count > 0 ? 'flex' : 'none';
    b.classList.add('animate-in');
    setTimeout(() => b.classList.remove('animate-in'), 500);
  });
}

window.updateCartCount = updateCartCount;

// ── Animate on Scroll ─────────────────────────────────────────────────────────
function initScrollAnimations() {
  const elements = document.querySelectorAll('[data-animate]');
  if (!elements.length || !('IntersectionObserver' in window)) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  elements.forEach(el => observer.observe(el));
}

// ── Flash Messages → Toasts ───────────────────────────────────────────────────
function initFlashMessages() {
  const messages = document.querySelectorAll('[data-message]');
  messages.forEach(el => {
    const msg = el.dataset.message;
    const type = el.dataset.type || 'info';
    if (msg) setTimeout(() => Toast.show(msg, type), 300);
    el.remove();
  });
}

// ── Navbar scroll effect ──────────────────────────────────────────────────────
function initNavbarScroll() {
  const navbar = document.querySelector('.navbar-shopsphere');
  if (!navbar) return;
  window.addEventListener('scroll', () => {
    if (window.scrollY > 60) {
      navbar.style.boxShadow = '0 8px 32px rgba(0,0,0,0.6)';
    } else {
      navbar.style.boxShadow = '0 4px 24px rgba(0,0,0,0.4)';
    }
  }, { passive: true });
}

// ── Gallery thumbnail switching ───────────────────────────────────────────────
function initProductGallery() {
  const thumbs = document.querySelectorAll('.gallery-thumb');
  const mainImg = document.getElementById('galleryMainImg');
  if (!thumbs.length || !mainImg) return;

  thumbs.forEach(thumb => {
    thumb.addEventListener('click', () => {
      const src = thumb.dataset.src;
      if (!src) return;
      thumbs.forEach(t => t.classList.remove('active'));
      thumb.classList.add('active');
      mainImg.style.opacity = '0';
      mainImg.style.transform = 'scale(0.96)';
      setTimeout(() => {
        mainImg.src = src;
        mainImg.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        mainImg.style.opacity = '1';
        mainImg.style.transform = 'scale(1)';
      }, 180);
    });
  });
}

// ── Quantity steppers ────────────────────────────────────────────────────────
function initQtySteppers() {
  document.querySelectorAll('.qty-stepper').forEach(wrapper => {
    const input = wrapper.querySelector('.qty-input');
    const minusBtn = wrapper.querySelector('[data-qty-minus]');
    const plusBtn = wrapper.querySelector('[data-qty-plus]');
    if (!input) return;

    const min = parseInt(input.min) || 1;
    const max = parseInt(input.max) || 9999;

    if (minusBtn) {
      minusBtn.addEventListener('click', () => {
        const v = Math.max(min, parseInt(input.value) - 1);
        input.value = v;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      });
    }

    if (plusBtn) {
      plusBtn.addEventListener('click', () => {
        const v = Math.min(max, parseInt(input.value) + 1);
        input.value = v;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      });
    }

    input.addEventListener('change', () => {
      let v = parseInt(input.value);
      if (isNaN(v) || v < min) v = min;
      if (v > max) v = max;
      input.value = v;
    });
  });
}

// ── Coupon form (checkout page) ───────────────────────────────────────────────
function initCouponForm() {
  const form = document.getElementById('couponForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = form.querySelector('[name="coupon_code"]');
    const btn = form.querySelector('[type="submit"]');
    const code = input ? input.value.trim() : '';
    if (!code) return;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-glow"></span>';

    try {
      const resp = await csrfFetch('/orders/coupon/apply/', {
        method: 'POST',
        body: JSON.stringify({ code }),
      });
      const data = await resp.json();
      if (data.success) {
        Toast.success(data.message);
        setTimeout(() => window.location.reload(), 800);
      } else {
        Toast.error(data.message);
      }
    } catch {
      Toast.error('Something went wrong. Please try again.');
    } finally {
      btn.disabled = false;
      btn.innerHTML = 'Apply';
    }
  });
}

// ── Real-Time Input Restriction ───────────────────────────────────────────────
function initRealTimeInputRestriction() {
  // Alphabet only (letters, spaces, hyphens)
  document.querySelectorAll('input[data-type="alphabet"]').forEach(input => {
    input.addEventListener('input', () => {
      input.value = input.value.replace(/[^A-Za-z\s\-]/g, '');
    });
  });

  // Numbers only (digits)
  document.querySelectorAll('input[data-type="number"]').forEach(input => {
    input.addEventListener('input', () => {
      input.value = input.value.replace(/[^0-9]/g, '');
    });
  });
}

// ── Escape HTML ───────────────────────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

// ── Init All ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initLiveSearch();
  initScrollAnimations();
  initFlashMessages();
  initNavbarScroll();
  initProductGallery();
  initQtySteppers();
  initCouponForm();
  initRealTimeInputRestriction();
});
