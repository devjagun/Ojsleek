#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

command -v docker >/dev/null 2>&1 || { echo "ERROR: docker not found"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 not found"; exit 1; }

if [ ! -d "$SCRIPT_DIR/_seed_data" ]; then
    mkdir -p "$SCRIPT_DIR/_seed_data"
fi

if [ ! -f "$SCRIPT_DIR/_seed_data/init.sql" ]; then
    cd "$SCRIPT_DIR"
    python3 generate_data.py
fi

docker compose -f "$COMPOSE_FILE" build --quiet

docker compose -f "$COMPOSE_FILE" up -d

echo "Waiting for postgres..."
for i in {1..30}; do
    if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U surehaul -d surehaul >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

echo "Waiting for gateway..."
for i in {1..30}; do
    if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

echo "Waiting for bonus-calc..."
for i in {1..30}; do
    if curl -sf http://localhost:9000/health >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

echo "Waiting for analytics..."
for i in {1..30}; do
    if curl -sf http://localhost:5000/health >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

curl -sf http://localhost:8080/health >/dev/null || { echo "FAIL: gateway not responding"; exit 1; }
curl -sf http://localhost:9000/health >/dev/null || { echo "FAIL: bonus-calc not responding"; exit 1; }
curl -sf http://localhost:5000/health >/dev/null || { echo "FAIL: analytics not responding"; exit 1; }

echo "All services ready"
exit 0
