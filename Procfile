release: python manage.py migrate
web: gunicorn dollarhive.wsgi:application --bind 0.0.0.0:$PORT
