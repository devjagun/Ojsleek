Analytics Service

This service provides reporting and analysis endpoints for SureHaul Logistics operational metrics.

Overview

The analytics service aggregates data from bonus payments, shifts, and fuel costs to provide insights into operational performance. It is the primary source for management reports and trend analysis.

Configuration

DATABASE_URL: PostgreSQL connection string. Defaults to postgres://surehaul:surehaul123@postgres:5432/surehaul

API Endpoints

GET /reports/bonus-summary
Returns aggregate bonus statistics for a date range.
Query parameters: start_date, end_date
Returns total payments, total paid, average bonus, min/max values, and average component values.

GET /reports/efficiency
Returns route efficiency metrics grouped by week, driver, or zone.
Query parameters: start_date, end_date, group_by (optional: week, driver, zone)
Returns efficiency ratios calculated as deliveries divided by targets.

GET /reports/fuel-impact
Returns weekly fuel costs alongside bonus payment data.
Query parameters: start_date, end_date
Use this report to analyze potential correlations between fuel prices and bonus amounts.

GET /metrics/comparison
Compares metrics between two time periods.
Query parameters: period1_start, period1_end, period2_start, period2_end
Returns metrics for each period plus percentage change calculations.

Notes on Data Interpretation

Efficiency ratio values above 1.0 indicate drivers completing more deliveries than targeted. Values below 1.0 indicate underperformance against targets.

Bonus amounts reflect the final calculated amounts from the bonus engine. The analytics service does not perform bonus calculations itself.

Fuel data is recorded daily by region. Weekly averages in reports are computed from daily values.
