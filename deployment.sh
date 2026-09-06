#!/bin/bash
# Run from the app root inside the cPanel virtualenv after uploading new code.
# (Migrations are committed with the code — never makemigrations on the server.)
set -e

pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Reload Passenger
mkdir -p tmp && touch tmp/restart.txt
echo "Deploy done."
