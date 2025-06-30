#!/usr/bin/env bash
# exit on error
# set -o errexit

# python3 -m pip install --upgrade pip

pip install -r requirements.txt

python3 manage.py collectstatic --no-input
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py save_urls_to_db
