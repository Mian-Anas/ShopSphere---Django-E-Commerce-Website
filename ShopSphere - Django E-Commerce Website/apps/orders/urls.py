"""
Orders URLs.
"""
from django.urls import path
from . import views
from .webhooks import stripe_webhook_view

app_name = 'orders'

urlpatterns = [
    path('', views.order_list_view, name='order_list'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('success/', views.order_success_view, name='success'),
    path('cancel/', views.order_cancel_view, name='cancel'),
    path('<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('<str:order_number>/invoice/', views.download_invoice_view, name='invoice'),
    path('coupon/apply/', views.apply_coupon_ajax, name='apply_coupon'),
    path('webhook/stripe/', stripe_webhook_view, name='stripe_webhook'),
]
