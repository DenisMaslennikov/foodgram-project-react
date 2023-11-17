#!/usr/bin/env bash

python /code/manage.py migrate --noinput

python /code/manage.py collectstatic --noinput

cp -r /static/django/. /static/

gunicorn --config python:gunicornconfig server.wsgi

