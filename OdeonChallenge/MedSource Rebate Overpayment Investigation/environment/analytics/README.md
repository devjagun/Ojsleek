# Analytics Service

This service provides reporting and analysis endpoints for the MedSource rebate management system.

## Overview

The analytics service aggregates data from the rebate payments database and provides various reports for business analysis. Reports can be filtered by quarter and customer segment.

## API Endpoints

### GET /health

Returns service health status.

### GET /reports/rebate-summary

Returns rebate totals grouped by customer class for a specified quarter.

Query parameters:
- quarter: Quarter string (e.g., "2024Q4"). Defaults to "2024Q4".

### GET /reports/variance-analysis

Returns quarter-over-quarter comparison of rebate totals with percentage changes. Useful for identifying trends and anomalies in rebate patterns.

### GET /reports/customer-detail/{customer_id}

Returns detailed information about a specific customer including their payment history and calculation audit log.

### GET /reports/hospital-impact

Returns data about hospital system contracts and their associated pharmacy volumes. Useful for analyzing the impact of hospital chain partnerships.

### GET /reports/seasonal-trends

Returns seasonal demand multipliers correlated with actual order volumes by product category. Useful for understanding seasonal patterns in purchasing.

### GET /reports/specialty-analysis

Returns analysis of specialty-certified pharmacies including their certification dates, specialty ratios, and rebate amounts.

### GET /reports/price-list-impact

Returns price list effectiveness data showing how many orders were processed under each price list version.

## Data Notes

The variance analysis report calculates percentage changes quarter-over-quarter. Null values in the previous quarter indicate it was the first quarter with data.

Specialty ratios represent the proportion of specialty product units to total units ordered during the quarter. A ratio of 0.35 means thirty five percent of units were specialty products.

Certification days in the specialty analysis represent the number of days from certification grant date to the current calculation date.

## Configuration

Database connection uses standard environment variables:
- DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
