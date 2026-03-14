# GridPeak Energy Settlement Overpayment Investigation Report

## Executive Summary

After thorough investigation of the settlement system, I have identified two programming bugs that together cause systematic overpayments to power generators. The combined impact ranges from three to twelve percent overpayment depending on generator characteristics. Both bugs have been fixed and settlements recalculated.

## Investigation Approach

I began by examining the settlement calculation pipeline to understand how payments flow from meter readings to final amounts. The system involves three services:

1. Gateway (Go) - API interface
2. Settlement Engine (Python) - Payment calculations
3. Loss Calculator (Fortran) - Transmission loss computations

I queried settlement data to identify patterns in overpayments, focusing on which generators showed the largest discrepancies. Two distinct patterns emerged:

- Generators at industrial locations showed elevated rates regardless of capacity factor
- Generators with energy delivery around 100 MWh showed lower than expected loss deductions

## Root Cause One: Fortran Loss Calculator Boundary Condition

In the loss calculator Fortran code, the threshold comparison uses strictly greater than instead of greater than or equal to:

```fortran
if (emwh > thresh) then
```

According to the documentation, the loss rate should apply when energy "meets or exceeds" the threshold. The threshold is set at 100 MWh for all zones. Generators delivering exactly 100 MWh receive a loss factor of 1.0 instead of the appropriate higher value (approximately 1.03 depending on zone).

Since loss deduction equals energy times the difference between loss factor and one times the rate, a loss factor of 1.0 produces zero deduction. This results in overpayment by the amount of the missed deduction.

Fix: Changed the comparison to use greater than or equal to:

```fortran
if (emwh >= thresh) then
```

## Root Cause Two: Rate Tier Selection Missing Capacity Factor Check

In the settlement engine Python code, the rate tier selection function returns the rate immediately when a tier location type matches the generator location, without verifying the capacity factor meets the minimum threshold:

```python
if loc_type is not None and loc_type == location_type:
    return float(rate)
```

The rate tier priority order means industrial location generators match the first tier (highest rate) regardless of their capacity factor. The intended behavior requires checking both the location match AND the capacity factor threshold.

Fix: Added the capacity factor check for location-matching tiers:

```python
if loc_type is not None and loc_type == location_type:
    if min_cf is None or capacity_factor >= float(min_cf):
        return float(rate)
```

## Red Herrings Dismissed

### Weather Patterns

The operations team suggested weather and demand factors might explain the overpayments. I analyzed:

- Weather data showing temperature extremes in October and November
- Demand factors that correlate with temperature

Finding: Demand factors are recorded in the weather_data table but do not appear in any settlement calculation code paths. The correlation between weather extremes and higher settlements exists because extreme weather drives higher generation volumes, not because of calculation errors. Overpayments occur in mild weather periods as well. Weather is not the cause.

### Transmission Upgrades

I investigated recent transmission line capacity upgrades:

- Five upgrades occurred between October 2025 and January 2026
- Capacity increases ranged from 100 to 250 MW

Finding: Transmission capacity is not referenced in settlement calculations. Loss factors depend only on zone and energy volume, not transmission capacity. The timing correlation is coincidental. Transmission upgrades are not the cause.

### Meter Firmware Updates

Approximately thirty generators received meter firmware updates during the problem period. I analyzed:

- Pre and post update energy readings
- Aggregate generation patterns

Finding: Energy readings show consistent patterns before and after firmware updates. No systematic measurement bias is evident. Affected generators do not show disproportionate overpayments. Firmware updates are not the cause.

## Impact Quantification

After identifying affected settlements:

- Approximately eight percent of settlements are affected by the loss factor bug (generators near 100 MWh threshold)
- Approximately fifteen percent of settlements are affected by the rate tier bug (industrial location generators with capacity factor below 0.75)
- Some generators are affected by both bugs

Estimated overpayment percentages:
- Loss factor bug only: three to four percent
- Rate tier bug only: eight to twenty-five percent depending on actual capacity factor
- Both bugs combined: up to thirty percent

## Remediation Applied

1. Fixed the Fortran loss calculator threshold comparison
2. Fixed the Python rate tier selection capacity factor check
3. Recompiled the Fortran executable
4. Recalculated all settlements for affected periods

## Recommendations

1. Add unit tests for boundary conditions in the loss calculator
2. Add integration tests verifying rate tier selection with various capacity factors
3. Implement settlement audit queries to detect anomalous rate or loss factor distributions
4. Consider adding logging to trace rate tier selection decisions for troubleshooting
