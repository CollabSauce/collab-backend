#!/bin/bash
set -euo pipefail

/app/docker/wait-for-it.sh -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -t 20 --strict -- echo "db is up"
/app/docker/wait-for-it.sh -h ${REDIS_HOST:-redis} -p ${REDIS_PORT:-6379} -t 20  --strict -- echo "redis is up"

exec "$@"
