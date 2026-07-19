"""
Orders Admin — Order with OrderItemInline, Mark as Shipped action.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_sku', 'price', 'quantity', 'get_total_price')

    def get_total_price(self, obj):
        if obj and obj.price is not None:
            return f'${obj.get_total_price():.2f}'
        return '$0.00'
    get_total_price.short_description = 'Total'


def mark_shipped(modeladmin, request, queryset):
    queryset.filter(status='paid').update(status='shipped')
mark_shipped.short_description = 'Mark selected orders as Shipped'


def mark_delivered(modeladmin, request, queryset):
    queryset.update(status='delivered')
mark_delivered.short_description = 'Mark selected orders as Delivered'


def mark_cancelled(modeladmin, request, queryset):
    queryset.update(status='cancelled')
mark_cancelled.short_description = 'Mark selected orders as Cancelled'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user', 'status_badge', 'total_amount',
        'coupon_code', 'stripe_payment_intent_id', 'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'user__username', 'user__email', 'stripe_payment_intent_id')
    readonly_fields = (
        'order_number', 'stripe_payment_intent_id', 'stripe_session_id',
        'created_at', 'updated_at'
    )
    inlines = [OrderItemInline]
    actions = [mark_shipped, mark_delivered, mark_cancelled]
    ordering = ('-created_at',)

    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'user', 'status', 'notes')
        }),
        ('Shipping Address', {
            'fields': (
                'shipping_full_name', 'shipping_address_line1', 'shipping_address_line2',
                'shipping_city', 'shipping_state', 'shipping_postal_code', 'shipping_country'
            )
        }),
        ('Billing Address', {
            'fields': (
                'billing_full_name', 'billing_address_line1', 'billing_address_line2',
                'billing_city', 'billing_state', 'billing_postal_code', 'billing_country'
            ),
            'classes': ('collapse',)
        }),
        ('Financials', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total_amount', 'coupon_code')
        }),
        ('Payment', {
            'fields': ('stripe_payment_intent_id', 'stripe_session_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        color_map = {
            'pending': '#f59e0b',
            'paid': '#3b82f6',
            'processing': '#8b5cf6',
            'shipped': '#06b6d4',
            'delivered': '#10b981',
            'cancelled': '#ef4444',
            'refunded': '#6b7280',
        }
        color = color_map.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;border-radius:12px;font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
