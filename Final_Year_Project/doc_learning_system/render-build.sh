#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python doc_learning_system/manage.py collectstatic --no-input
python doc_learning_system/manage.py migrate