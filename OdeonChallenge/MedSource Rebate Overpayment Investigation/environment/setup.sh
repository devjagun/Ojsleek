#!/bin/bash
set -e

echo "==================================="
echo "MedSource Rebate Investigation Setup"
echo "==================================="

# Navigate to environment directory
cd "$(dirname "$0")"

# Stop any existing containers
echo "Stopping existing containers..."
docker compose down -v 2>/dev/null || true

# Build all services
echo "Building services..."
docker compose build --no-cache

# Start all services
echo "Starting services..."
docker compose up -d

# Wait for health checks
echo "Waiting for services to be ready..."
sleep 5

# Check health
./healthcheck.sh

echo ""
echo "==================================="
echo "Setup complete!"
echo "==================================="
echo ""
echo "Services available at:"
echo "  Gateway API:    http://localhost:9000"
echo "  Rebate Engine:  http://localhost:5001"
echo "  Analytics:      http://localhost:5002"
echo "  PostgreSQL:     localhost:5432"
echo ""
echo "Database credentials:"
echo "  User: medsource"
echo "  Password: medsource123"
echo "  Database: medsource"
echo ""
