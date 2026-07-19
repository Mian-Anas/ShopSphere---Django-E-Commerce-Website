"""
Cart Admin — Cart, CartItem, Wishlist.
"""
from django.contrib import admin
from .models import Cart, CartItem, Wishlist


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('added_at', 'get_total_price')

    def get_total_price(self, obj):
        return f'${obj.get_total_price():.2f}'
    get_total_price.short_description = 'Total'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'session_id', 'total_items', 'subtotal', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'session_id')
    inlines = [CartItemInline]
    readonly_fields = ('created_at', 'updated_at')

    def total_items(self, obj):
        return obj.get_total_items()
    total_items.short_description = 'Items'

    def subtotal(self, obj):
        return f'${obj.get_subtotal():.2f}'
    subtotal.short_description = 'Subtotal'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'product__name')
    raw_id_fields = ('user', 'product')
