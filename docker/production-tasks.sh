#!/bin/bash
set -euo pipefail

# python manage.py collectstatic --noinput DONT DO DOESNT WORK. DO IT IN DOCKERFILE
python manage.py migrate
