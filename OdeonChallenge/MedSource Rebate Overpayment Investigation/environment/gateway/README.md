# API Gateway

This service provides a unified entry point for the MedSource rebate management system.

## Overview

The gateway routes requests to the appropriate backend services and provides health monitoring for the system.

## Endpoints

### GET /health

Returns gateway health status and upstream service availability.

Response:
```json
{
  "status": "healthy",
  "service": "gateway",
  "upstream": {
    "rebate-engine": "healthy",
    "analytics": "healthy"
  }
}
```

### /api/rebate/*

Proxies requests to the rebate calculation engine.

Examples:
- POST /api/rebate/calculate - Calculate single rebate
- POST /api/rebate/batch-calculate - Process all pending rebates

### /api/analytics/*

Proxies requests to the analytics service.

Examples:
- GET /api/analytics/reports/rebate-summary?quarter=2024Q4
- GET /api/analytics/reports/variance-analysis
- GET /api/analytics/reports/customer-detail/1

## Configuration

Environment variables:
- REBATE_ENGINE_URL: Base URL for rebate engine (default: http://rebate-engine:5001)
- ANALYTICS_URL: Base URL for analytics service (default: http://analytics:5002)

## Port

The gateway listens on port 9000.
