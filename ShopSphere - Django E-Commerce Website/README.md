# 🛍️ ShopSphere — Premium Django E-Commerce Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0%2B-092E20?style=flat-square&logo=django&logoColor=white)
![Stripe](https://img.shields.io/badge/Stripe-Payments-635BFF?style=flat-square&logo=stripe&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=flat-square&logo=bootstrap&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**A full-featured, production-ready e-commerce platform built with Django 5, Stripe payments, and a stunning dark glassmorphism UI.**

</div>

---

## ✨ Features

### 🏪 Store
- **Product Catalog** — Browse products with categories, brands, search, and multi-criteria filtering
- **Product Detail** — Image gallery, reviews, ratings, related products, breadcrumb navigation
- **Live Search** — Instant AJAX autocomplete with debounced queries
- **Pagination** — Paginated product listings with filter persistence

### 🛒 Shopping Cart
- **AJAX Cart** — Add, update, remove items without page reload
- **Guest Cart** — Session-based cart for unauthenticated users (merged on login)
- **Wishlist** — Save products for later with one-click toggle
- **Move to Cart** — Transfer wishlist items directly to cart

### 💳 Checkout & Payments
- **Stripe Checkout** — Secure payment processing via Stripe Checkout Sessions
- **Coupon System** — Percentage and fixed-amount discount codes with validation
- **Order Summary** — Real-time tax calculation, shipping fees, and discount breakdown
- **Webhook Handler** — Secure Stripe webhook for payment confirmation, stock deduction, and cart clearing

### 📦 Orders
- **Order Management** — Track orders with status progression (Pending → Paid → Shipped → Delivered)
- **Order History** — View all past orders with details
- **PDF Invoices** — Auto-generated branded PDF invoices via ReportLab
- **Admin Actions** — Bulk mark as shipped/delivered/cancelled from Django admin

### 👤 Accounts
- **Registration & Login** — Full auth flow with email validation
- **Profile Management** — Update personal info, avatar, and bio
- **Address Book** — Multiple shipping/billing addresses with default selection
- **Password Reset** — Email-based password reset flow
- **Order History** — View order history from profile

### 🎨 Design
- **Dark Glassmorphism UI** — Premium dark theme with glass effects, gradients, and micro-animations
- **Responsive Layout** — Fully responsive across mobile, tablet, and desktop
- **Custom Toast Notifications** — Beautiful animated notifications for all user actions
- **Inter + Outfit Typography** — Modern Google Fonts for a premium feel
- **Bootstrap 5** — Solid foundation with custom CSS overrides

### 🔧 Technical
- **Split Settings** — Separate `dev.py` / `prod.py` settings with shared `base.py`
- **Environment Variables** — All secrets via `.env` (python-dotenv)
- **WhiteNoise** — Static file serving for production
- **Signals** — Auto slug generation, auto profile creation
- **Context Processors** — Global cart count and category navigation
- **Comprehensive Admin** — Rich Django admin with inlines, filters, and custom actions
- **Unit Tests** — 41 tests covering models, views, and AJAX endpoints

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ (tested on 3.14)
- pip or uv package manager
- Stripe account (for payments)

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/shopsphere.git
cd shopsphere
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your settings:
# - SECRET_KEY (generate a new one)
# - STRIPE_PUBLIC_KEY & STRIPE_SECRET_KEY (from Stripe Dashboard)
# - STRIPE_WEBHOOK_SECRET (from Stripe CLI or Dashboard)
# - EMAIL settings (optional, console backend by default)
```

### 5. Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data    # Populate with demo products
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000** 🎉

---

## 📁 Project Structure

```
ShopSphere/
├── apps/
│   ├── accounts/          # User auth, profile, addresses
│   │   ├── models.py      # Profile, Address
│   │   ├── views.py       # Login, Register, Profile, Password
│   │   ├── forms.py       # Custom auth & profile forms
│   │   ├── signals.py     # Auto-create Profile on User creation
│   │   ├── admin.py       # Profile inline in UserAdmin
│   │   └── tests.py       # 6 tests
│   │
│   ├── store/             # Product catalog & reviews
│   │   ├── models.py      # Category, Brand, Product, ProductImage, Coupon, Review
│   │   ├── views.py       # Home, Shop, Product Detail, Search API, Reviews
│   │   ├── signals.py     # Auto-slug generation
│   │   ├── admin.py       # Rich admin with inlines & actions
│   │   ├── management/commands/seed_data.py
│   │   └── tests.py       # 13 tests
│   │
│   ├── cart/              # Shopping cart & wishlist
│   │   ├── models.py      # Cart, CartItem, Wishlist
│   │   ├── views.py       # AJAX add/update/remove, wishlist toggle
│   │   ├── context_processors.py  # Global cart count
│   │   ├── admin.py       # Cart admin with item inline
│   │   └── tests.py       # 10 tests
│   │
│   └── orders/            # Checkout, payments, invoices
│       ├── models.py      # Order, OrderItem
│       ├── views.py       # Checkout flow, Stripe session, order detail
│       ├── webhooks.py    # Stripe webhook handler
│       ├── utils.py       # Invoice PDF generation, order totals
│       ├── admin.py       # Order admin with status badges
│       └── tests.py       # 6 tests
│
├── shopsphere/            # Django project config
│   ├── settings/
│   │   ├── base.py        # Shared settings
│   │   ├── dev.py         # Development (SQLite, DEBUG=True)
│   │   └── prod.py        # Production (security headers)
│   ├── urls.py            # Root URL config
│   └── wsgi.py / asgi.py
│
├── templates/             # Django templates
│   ├── base.html          # Master layout (navbar, footer, toast system)
│   ├── 404.html / 500.html
│   ├── store/             # Home, shop, product detail
│   ├── accounts/          # Auth pages, profile, addresses
│   ├── cart/              # Cart, wishlist
│   └── orders/            # Checkout, success, cancel, order detail
│
├── static/
│   ├── css/style.css      # 1650+ lines of premium dark theme CSS
│   ├── js/main.js         # Toast system, live search, animations
│   └── js/cart.js         # AJAX cart & wishlist operations
│
├── manage.py
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 🧪 Running Tests

```bash
python manage.py test
```

All 41 tests should pass. One test uses `raise_request_exception=False` to work around a known Python 3.14 + Django 5.1 template context copy issue.

---

## 💳 Stripe Setup

1. Create a [Stripe account](https://stripe.com)
2. Get your **test** API keys from the [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys)
3. Add them to `.env`:
   ```
   STRIPE_PUBLIC_KEY=pk_test_...
   STRIPE_SECRET_KEY=sk_test_...
   ```
4. For webhooks, use the [Stripe CLI](https://stripe.com/docs/stripe-cli):
   ```bash
   stripe listen --forward-to localhost:8000/orders/webhook/stripe/
   ```
5. Copy the webhook signing secret to `.env`:
   ```
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

---

## 🛠️ Management Commands

| Command | Description |
|---------|-------------|
| `python manage.py seed_data` | Populate DB with demo categories, brands, and 16 products |
| `python manage.py createsuperuser` | Create admin account |
| `python manage.py collectstatic` | Collect static files for production |

---

## 📝 Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Django 5.x** | Web framework |
| **SQLite** | Database (dev), swappable to PostgreSQL |
| **Stripe** | Payment processing |
| **Bootstrap 5.3** | CSS framework foundation |
| **ReportLab** | PDF invoice generation |
| **WhiteNoise** | Static file serving |
| **python-dotenv** | Environment variable management |
| **Pillow** | Image handling |

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

<div align="center">
  <p>Built with ❤️ using Django</p>
  <p><strong>ShopSphere</strong> — Shop the Future of Retail</p>
</div>
