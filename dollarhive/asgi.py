"""
ASGI config for the dollarhive project.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dollarhive.settings')

application = get_asgi_application()
