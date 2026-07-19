"""
Store Signals — auto-generate slugs for Category, Brand, Product.
"""
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Category, Brand, Product


def _unique_slug(model_class, value, instance):
    """Generate a unique slug for a given model, appending a counter if needed."""
    slug = slugify(value)
    if not slug:
        slug = 'item'
    qs = model_class.objects.filter(slug__startswith=slug)
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
    if not qs.filter(slug=slug).exists():
        return slug
    counter = 1
    while True:
        candidate = f'{slug}-{counter}'
        if not qs.filter(slug=candidate).exists():
            return candidate
        counter += 1


@receiver(pre_save, sender=Category)
def auto_slug_category(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = _unique_slug(Category, instance.name, instance)


@receiver(pre_save, sender=Brand)
def auto_slug_brand(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = _unique_slug(Brand, instance.name, instance)


@receiver(pre_save, sender=Product)
def auto_slug_product(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = _unique_slug(Product, instance.name, instance)
