release: python manage.py migrate
web: gunicorn collab.wsgi:application --bind 0.0.0.0:$PORT --log-file -
worker: celery -A collab worker -l info
