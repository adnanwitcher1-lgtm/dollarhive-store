"""
WSGI config for the dollarhive project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dollarhive.settings')

application = get_wsgi_application()
