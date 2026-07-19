"""
ASGI config for ShopSphere project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopsphere.settings.dev')
application = get_asgi_application()
