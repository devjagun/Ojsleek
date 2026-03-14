# Gateway Service

This service provides the primary API interface for the GridPeak settlement system.

## Overview

The gateway is a Go application that handles all external API requests. It provides endpoints for querying generators, nodes, settlements, and reference data. It also proxies settlement calculation requests to the settlement engine.

## Endpoints

See endpoints.md for the complete API reference.

## Data Access

The gateway connects directly to the PostgreSQL database for read operations. It joins relevant tables to provide enriched responses where appropriate.

## Settlement Proxy

Settlement calculation requests are forwarded to the settlement engine service. The gateway does not perform any settlement calculations itself.

## Query Parameters

Most list endpoints support filtering via query parameters. Date filters use ISO 8601 format. Numeric filters use standard integers.

## Response Format

All responses are JSON formatted. List endpoints return arrays. Single item endpoints return objects.

## Error Handling

The gateway returns standard HTTP status codes. 200 for success, 404 for not found, 500 for server errors.
