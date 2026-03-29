# GridPeak Energy Markets API Reference

## Gateway Service

Base URL: http://localhost:8080

### Health Check

GET /health

Returns service health status.

### Generators

GET /api/generators

Returns all generators with their node information.

GET /api/generators/{id}

Returns a specific generator by ID.

### Nodes

GET /api/nodes

Returns all grid nodes with zone and congestion information.

### Settlements

GET /api/settlements

Query parameters:
- generator_id: Filter by generator
- period_start: Filter settlements starting on or after this date
- period_end: Filter settlements ending on or before this date

GET /api/settlements/summary

Returns aggregated settlement data grouped by generator type and zone.

Query parameters:
- period_start: Start date filter
- period_end: End date filter

### Settlement Energy Analysis

GET /api/settlements/energy_analysis

Returns settlement statistics grouped by energy MWh bucket (25 MWh intervals). Each bucket includes average and minimum loss factors, loss deduction totals, count of settlements with unity loss factor, and net payment aggregates. Useful for identifying anomalies in loss factor application across different energy delivery volumes.

### Settlement Data Quality Analysis

GET /api/settlements/data_quality_analysis

Returns settlement metrics grouped by data quality status and location type. Classifies each generator as either "has_flagged_readings" (any meter readings with non-null quality flags like DECOMMISSIONED, ESTIMATED, INTERPOLATED, etc.) or "clean_only" (all readings have null quality flags). For each group and location type, shows settlement count, average rate applied, average loss factor, count of unity loss factor settlements, average and total net payments, and average capacity factor. Useful for determining whether meter reading data quality flags correlate with settlement anomalies.

### Meter Readings

GET /api/meter_readings

Query parameters:
- generator_id: Filter by generator
- start: Start timestamp
- end: End timestamp
- limit: Maximum number of records

### Reference Data

GET /api/loss_factors

Returns transmission loss factors by zone.

GET /api/rate_tiers

Returns rate tier configurations for each generator type.

### Environmental Data

GET /api/weather

Query parameters:
- zone: Filter by zone
- start: Start timestamp
- end: End timestamp

GET /api/transmission_upgrades

Returns transmission line upgrade history.

GET /api/meter_firmware

Returns meter firmware update history.

### Settlement Calculation

POST /api/calculate

Request body:
```
{
    "generator_id": 1,
    "period_start": "2025-10-01T00:00:00",
    "period_end": "2025-10-08T00:00:00"
}
```

POST /api/recalculate_all

Recalculates settlements for all active generators in the specified period.

Request body:
```
{
    "period_start": "2025-10-01T00:00:00",
    "period_end": "2025-10-08T00:00:00"
}
```

## Settlement Engine Service

Base URL: http://localhost:8082

### Health Check

GET /health

### Calculate Settlement

POST /calculate

Calculates settlement for a single generator.

POST /batch_calculate

Calculates settlements for multiple generators.

POST /recalculate_all

Clears and recalculates all settlements for a period.

## Loss Calculator Service

Base URL: http://localhost:8081

### Health Check

GET /health

### Calculate Loss Factor

POST /calculate

Request body:
```
{
    "zone": "NORTH",
    "energy_mwh": 150.5
}
```

Returns the computed loss factor for the given zone and energy amount.

POST /batch_calculate

Calculates loss factors for multiple items.
