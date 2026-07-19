"""
Store Context Processor — expose categories and brands globally.
"""
from .models import Category, Brand


def store_context(request):
    return {
        'nav_categories': Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('children'),
        'nav_brands': Brand.objects.filter(is_active=True)[:10],
    }
