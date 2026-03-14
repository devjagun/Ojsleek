#!/bin/bash

echo "Checking service health..."
echo ""

MAX_RETRIES=30
RETRY_INTERVAL=2

check_service() {
    local name=$1
    local url=$2
    local retries=0
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo "✓ $name is healthy"
            return 0
        fi
        retries=$((retries + 1))
        sleep $RETRY_INTERVAL
    done
    
    echo "✗ $name failed to start"
    return 1
}

# Check PostgreSQL
echo -n "Checking PostgreSQL... "
retries=0
while [ $retries -lt $MAX_RETRIES ]; do
    if docker exec postgres pg_isready -U medsource -d medsource > /dev/null 2>&1; then
        echo "✓ PostgreSQL is healthy"
        break
    fi
    retries=$((retries + 1))
    sleep $RETRY_INTERVAL
done
if [ $retries -eq $MAX_RETRIES ]; then
    echo "✗ PostgreSQL failed to start"
    exit 1
fi

# Check other services
check_service "Rebate Engine" "http://localhost:5001/health"
check_service "Analytics" "http://localhost:5002/health"
check_service "Gateway" "http://localhost:9000/health"

echo ""
echo "All services are healthy!"
