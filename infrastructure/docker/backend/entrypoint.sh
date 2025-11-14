#!/bin/bash
set -e

echo "🚀 Starting Santé Medical Backend..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until pg_isready -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-sante_user}; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "✅ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
until timeout 1 bash -c "cat < /dev/null > /dev/tcp/${REDIS_HOST:-redis}/${REDIS_PORT:-6379}"; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done
echo "✅ Redis is ready!"

# Run database migrations
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "📦 Running Alembic migrations..."
    alembic upgrade head
    echo "✅ Migrations complete!"
fi

# Execute CMD
echo "🎉 Starting application..."
exec "$@"
