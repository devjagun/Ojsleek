Gateway Service

This service provides the main API gateway for SureHaul Logistics external integrations. It handles request routing, authentication, and aggregates data from underlying services.

Overview

The gateway exposes REST endpoints for accessing driver information, zone data, and route summaries. It connects directly to the PostgreSQL database for read operations.

Architecture

Built in Go for performance and low memory footprint. Uses standard library HTTP server with slog for structured JSON logging.

Configuration

DATABASE_URL: PostgreSQL connection string. Defaults to postgres://surehaul:surehaul123@postgres:5432/surehaul

The service attempts database connection up to 30 times with 2 second intervals before failing.

API Endpoints

GET /health
Returns service health status.

GET /api/drivers
Returns all drivers with basic information.

GET /api/drivers/{id}
Returns single driver details.

GET /api/drivers/{id}/shifts
Returns shift history for a driver. Requires start_date and end_date query parameters.

GET /api/zones
Returns all active delivery zones.

GET /api/routes/summary
Returns aggregate route statistics. Requires start_date and end_date query parameters. Returns total shifts, total deliveries, efficiency ratio.

Development

Requires Go 1.21 or later. Build with go build -o gateway main.go and run with ./gateway.
