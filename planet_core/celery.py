import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'planet_core.settings')

# Initialize the Celery app
app = Celery('planet_core')

# Load config from Django settings, using a 'CELERY_' namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover 'tasks.py' in all installed apps
app.autodiscover_tasks()
