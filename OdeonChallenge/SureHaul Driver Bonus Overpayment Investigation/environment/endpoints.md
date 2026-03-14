SureHaul Logistics API Reference

This document describes the available API endpoints across our microservices.

Gateway Service

Base URL: http://gateway:8080

GET /health
Returns service health status.

GET /api/drivers
Returns list of all drivers with basic info.
Response contains driver_id, name, hire_date, tier, and status fields.

GET /api/drivers/{driver_id}
Returns details for a specific driver.

GET /api/drivers/{driver_id}/shifts
Returns shift history for a driver.
Query parameters: start_date, end_date

GET /api/zones
Returns all delivery zones with their difficulty ratings.
Response contains zone_id, zone_name, base_difficulty, and region fields.

GET /api/routes/summary
Returns route summary statistics.
Query parameters: start_date, end_date

Bonus Calculator Service

Base URL: http://bonus-calc:9000

GET /health
Returns service health status.

GET /calculate/{driver_id}
Calculates bonus for a driver for the specified period.
Query parameters: period_start, period_end
Returns the calculated bonus amount and score breakdown.

GET /scores/{driver_id}/breakdown
Returns detailed Driver Efficiency Bonus Score breakdown.
Query parameters: shift_date

POST /batch-calculate
Triggers batch calculation of bonuses.
Body: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}

Analytics Service

Base URL: http://analytics:5000

GET /health
Returns service health status.

GET /reports/bonus-summary
Returns bonus payment summary statistics.
Query parameters: start_date, end_date

GET /reports/efficiency
Returns route efficiency metrics.
Query parameters: start_date, end_date, group_by (optional: driver, zone, week)

GET /reports/fuel-impact
Returns fuel cost analysis.
Query parameters: start_date, end_date

GET /metrics/comparison
Compares metrics between two periods.
Query parameters: period1_start, period1_end, period2_start, period2_end

Database

PostgreSQL is available at postgres:5432
Database name: surehaul
Username: surehaul
Password: surehaul123

Available tables:

drivers
Contains driver information.
Columns: driver_id, name, hire_date, tier, status, region

shifts
Contains shift records.
Columns: shift_id, driver_id, shift_date, zone_id, start_time, end_time, deliveries_completed, route_target, break_minutes

zones
Contains zone definitions.
Columns: zone_id, zone_name, base_difficulty, region, active

feedback
Contains customer feedback ratings.
Columns: feedback_id, driver_id, zone_id, rating, feedback_date

bonus_payments
Contains bonus payment records.
Columns: payment_id, driver_id, shift_date, base_performance_index, zone_difficulty_factor, tier_multiplier, final_score, bonus_amount, calculated_at, paid_at

fuel_costs
Contains daily fuel cost records.
Columns: date, region, price_per_gallon, weekly_average

driver_zone_history
Contains driver zone assignment history.
Columns: driver_id, zone_id, first_worked_date, total_days_in_zone
