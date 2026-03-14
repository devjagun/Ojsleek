# Settlement Engine Service

This service calculates settlement payments for power generators.

## Overview

The settlement engine is responsible for computing accurate payments to generators based on their electricity deliveries. It coordinates with the loss calculator service and accesses rate tier configurations to determine final payment amounts.

## Settlement Calculation

For each settlement period, the engine performs these steps:

Aggregate meter readings to compute total energy delivered in megawatt hours. Readings are converted from megawatts using the interval duration.

Calculate the capacity factor by dividing actual generation by theoretical maximum. Theoretical maximum equals rated capacity times hours in period.

Select the appropriate rate tier based on generator type and characteristics.

Compute gross payment as energy multiplied by rate.

Request loss factor from the loss calculator service.

Apply loss deduction as energy times loss factor minus one times rate.

Add congestion credit based on node congestion factor.

Derive net payment from gross minus loss deduction plus congestion credit.

## Rate Tier Selection

The rate tier selection algorithm follows priority order rules. Rate tiers are stored with a priority number where lower numbers have higher priority.

For a given generator type, fetch all applicable tiers sorted by priority. For each tier in order, check if the generator meets the criteria. The first matching tier determines the rate.

Tier criteria can include:

Location type requirement. If specified, the generator node must have this location type.

Minimum capacity factor. If specified, the calculated capacity factor must meet or exceed this threshold.

When a criterion is null, it does not restrict matching. A tier with null location type matches any location. A tier with null minimum capacity factor matches any capacity factor.

## Rounding Rules

Energy aggregation uses four decimal place precision with half up rounding for intermediate values. The final energy total is rounded to two decimal places.

Payment amounts are rounded to two decimal places.

## Database Tables

The engine reads from generators, nodes, meter_readings, loss_factors, and rate_tiers tables. It writes to the settlements table.

## API Endpoints

POST /calculate processes a single generator settlement.

POST /batch_calculate processes multiple generators.

POST /recalculate_all clears existing settlements for a period and recalculates all active generators.
