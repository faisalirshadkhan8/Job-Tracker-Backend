web: gunicorn --bind 0.0.0.0:$PORT config.wsgi:application --workers 3 --threads 2 --timeout 120
celery_worker: celery -A config worker -l info --concurrency=2
celery_beat: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
