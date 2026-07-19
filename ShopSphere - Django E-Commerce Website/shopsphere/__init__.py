"""
ShopSphere Django Project
"""
import sys

# Patch django.template.context.BaseContext.__copy__ to fix Python 3.14 compatibility issue.
# In Python 3.14, `copy(super())` used in Django's BaseContext.__copy__ fails with
# AttributeError: 'super' object has no attribute 'dicts'.
try:
    import django.template.context
    def patched_copy(self):
        cls = self.__class__
        duplicate = cls.__new__(cls)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate
    django.template.context.BaseContext.__copy__ = patched_copy
except Exception as e:
    pass
