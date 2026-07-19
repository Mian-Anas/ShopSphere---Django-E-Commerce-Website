"""
WSGI config for ShopSphere project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopsphere.settings.dev')
application = get_wsgi_application()
