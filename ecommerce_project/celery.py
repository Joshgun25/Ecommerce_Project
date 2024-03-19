from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from datetime import timedelta


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')

app = Celery('ecommerce_project')

app.conf.beat_schedule = {
    'deactivate-expired-products': {
        'task': 'products.tasks.deactivate_expired_products',
        'schedule': timedelta(seconds=1),  # Run every second
    },
}


app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
