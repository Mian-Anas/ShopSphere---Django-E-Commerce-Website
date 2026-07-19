"""
Store Admin — Category, Brand, Product (with image inline), Coupon, Review.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Brand, Product, ProductImage, Coupon, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'slug', 'is_active', 'products_count')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

    def products_count(self, obj):
        return obj.get_products_count()
    products_count.short_description = 'Products'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'logo_preview', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height:50px;max-width:120px;object-fit:contain;"/>',
                obj.logo.url
            )
        return '—'
    logo_preview.short_description = 'Logo'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ('image', 'alt_text', 'is_primary', 'order', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:80px;max-width:120px;object-fit:contain;"/>',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Preview'


def mark_featured(modeladmin, request, queryset):
    queryset.update(is_featured=True)
mark_featured.short_description = 'Mark selected products as Featured'


def unmark_featured(modeladmin, request, queryset):
    queryset.update(is_featured=False)
unmark_featured.short_description = 'Remove Featured status from selected products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'sku', 'category', 'brand', 'price', 'discount_price',
        'stock', 'is_active', 'is_featured', 'primary_image_preview', 'created_at'
    )
    list_filter = ('is_active', 'is_featured', 'category', 'brand', 'created_at')
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('category', 'brand')
    inlines = [ProductImageInline]
    actions = [mark_featured, unmark_featured]
    list_editable = ('is_active', 'is_featured', 'stock')
    ordering = ('-created_at',)
    readonly_fields = ('sku', 'created_at', 'updated_at')

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'sku', 'category', 'brand', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'discount_price', 'stock')
        }),
        ('Visibility', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def primary_image_preview(self, obj):
        img = obj.get_primary_image()
        if img:
            return format_html(
                '<img src="{}" style="max-height:60px;max-width:80px;object-fit:contain;"/>',
                img.image.url
            )
        return '—'
    primary_image_preview.short_description = 'Image'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'is_active', 'active_from', 'active_to', 'used_count')
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code',)
    list_editable = ('is_active',)


def approve_reviews(modeladmin, request, queryset):
    queryset.update(is_approved=True)
approve_reviews.short_description = 'Approve selected reviews'


def reject_reviews(modeladmin, request, queryset):
    queryset.update(is_approved=False)
reject_reviews.short_description = 'Reject selected reviews'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')
    actions = [approve_reviews, reject_reviews]
    list_editable = ('is_approved',)
    raw_id_fields = ('product', 'user')
