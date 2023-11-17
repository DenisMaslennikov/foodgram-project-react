#!/usr/bin/env bash

python /code/manage.py migrate --noinput

python /code/manage.py collectstatic --noinput

cp -r /static/django/. /static/

python /code/manage.py runserver 0.0.0.0:8000

