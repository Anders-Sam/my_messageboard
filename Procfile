web: gunicorn my_messageboard.wsgi --log-file - --log-level info
release: echo "ATTEMPTING RELEASE COMMAND AT $(date)" && python manage.py migrate
