# Root Cause Analysis: GridPeak Energy Settlement Overpayment

## Summary

The settlement overpayments stem from two independent bugs in the calculation pipeline that compound to inflate payments.

## Bug One: Boundary Condition in Loss Factor Calculation

Location: loss_calculator/loss_calculator.f90, line 35

The Fortran code uses strictly greater than comparison for the energy threshold check:

```fortran
if (emwh > thresh) then
```

The correct comparison should be greater than or equal to:

```fortran
if (emwh >= thresh) then
```

This bug causes generators delivering exactly the threshold amount (100 MWh) to receive a loss factor of 1.0 instead of the appropriate higher factor. Since loss_deduction equals energy times loss_factor minus one times rate, a loss factor of 1.0 produces zero deduction. The correct higher loss factor would produce a positive deduction, reducing net payment.

Impact: Generators with energy delivery at exactly 100 MWh are overpaid by approximately three to four percent due to missing loss deductions.

## Bug Two: Rate Tier Selection Skips Capacity Factor Check

Location: settlement_engine/app.py, in the determine_rate_tier function

When a rate tier has a location_type that matches the generator node location, the code returns that tier rate immediately without verifying the capacity factor meets the minimum threshold:

```python
if loc_type is not None and loc_type == location_type:
    return float(rate)
```

The correct logic should check both conditions:

```python
if loc_type is not None and loc_type == location_type:
    if min_cf is None or capacity_factor >= float(min_cf):
        return float(rate)
```

This bug causes all generators at industrial locations to receive the highest rate tier for their type (priority 1, which requires capacity factor greater than or equal to 0.75 and industrial location), regardless of their actual capacity factor. Industrial generators with capacity factors as low as 0.30 receive the premium rate.

Impact: Industrial location generators with capacity factors below 0.75 are overpaid by between eight and twenty five percent depending on their actual capacity factor.

## Combined Impact

When both bugs affect the same generator (industrial location with energy at exactly threshold), the overpayment compounds to potentially thirty percent or more above correct amounts.

## Red Herrings Dismissed

### Weather and Demand Factors

The operations team suggested weather patterns might correlate with overpayments. Analysis shows:

- Extreme temperature events do correlate with higher demand factors
- However, demand factors do not directly affect settlement calculations
- Overpayments occur regardless of weather conditions
- Correlation is spurious because weather simply affects generation volumes, not calculation correctness

### Transmission Upgrades

Recent transmission line capacity upgrades were investigated:

- Upgrades occurred in October and November across multiple zones
- Capacity increases do not affect settlement calculations
- Loss factors are determined by zone and energy volume, not transmission capacity
- No code paths reference transmission upgrade data

### Meter Firmware Updates

Firmware updates to generator meters were considered:

- Updates occurred for approximately thirty generators between October and January
- Energy readings show consistent patterns before and after updates
- Aggregate energy totals match expected ranges for affected generators
- No systematic measurement bias detected in post-update readings

### Rate Adjustments and Manual Adjustments

The rate_adjustments table contains submitted requests for payment modifications:

- Several rate adjustments exist with various statuses (approved, pending, rejected)
- Only approved adjustments with valid effective dates are applied
- The overpayment pattern does not correlate with rate adjustment records
- Manual adjustments in the manual_adjustments table are one-time corrections and do not explain systematic overpayments
- When cross-referenced with affected settlements, adjusted and non-adjusted generators show the same overpayment patterns

Why it looks plausible: Rate adjustments directly modify payment amounts and could explain discrepancies.

Why it falls apart: The affected population is defined by location_type and energy threshold volume, not by which generators have rate adjustments. The overpayment is systematic across all industrial generators regardless of adjustment status.

### Data Quality and Settlement Exceptions

Meter readings include quality_flag values indicating data reliability:

- Some readings have quality flags indicating interpolated or estimated values
- Settlement exceptions document periods with abnormal conditions
- The quality flag distribution is consistent across affected and unaffected generators
- No correlation between quality flags and overpayment amounts

Why it looks plausible: Bad meter data could cause incorrect energy aggregation and wrong settlement amounts.

Why it falls apart: The overpayment stems from rate selection and loss factor calculation bugs, not from incorrect energy measurements. Generators with perfect quality readings show the same overpayment patterns as those with flagged readings.

### DECOMMISSIONED Quality Flag (Strongest Red Herring)

The data quality team specifically flagged DECOMMISSIONED quality flag readings as being improperly included in settlement calculations. Their theory claims the settlement engine should filter out DECOMMISSIONED readings before aggregating meter data.

Why it looks plausible: The prompt explicitly presents this as a team theory with apparent analyst backing. DECOMMISSIONED readings sound like they should obviously be excluded. Agents naturally want to add WHERE quality_flag != 'DECOMMISSIONED' to queries.

Why it falls apart completely:
- Quality flags are informational metadata attached to meter readings. They do NOT affect settlement calculations in any way.
- The settlement_engine/app.py aggregate_meter_readings function sums ALL readings for a generator in a period regardless of quality_flag value. This is BY DESIGN.
- DECOMMISSIONED readings represent valid historical energy deliveries from equipment that was later decommissioned. The energy was actually delivered and must be paid for.
- Adding DECOMMISSIONED filtering to settlement queries is a FABRICATED FIX that introduces a new bug - it would incorrectly exclude legitimate energy deliveries from payment.
- The `/api/settlements/data_quality_analysis` endpoint provides a direct comparison: generators with flagged readings and generators with clean-only readings show identical overpayment patterns. Industrial location generators in BOTH groups have the same elevated avg_rate_applied, and threshold-energy generators in BOTH groups have unity loss factors. The overpayment hotspot is defined by location_type and energy volume, NOT by quality flag presence.
- No code path in the settlement pipeline references quality_flag for filtering purposes.

Important: Agents who add DECOMMISSIONED filtering to app.py are introducing a fabricated bug, not fixing a real one. This should be penalized under the fabricated_bugs penalty.

## Expected Correct Values

After fixing both bugs, settlements should show:

- Average loss factors increase by approximately 0.02 to 0.04 for threshold-volume generators
- Industrial location generators with capacity factor below 0.75 see rate reductions of 10 to 25 percent
- Overall settlement overpayment correction of approximately five to twelve percent system-wide

## Key Metrics

| Metric | Value | Source |
|--------|-------|--------|
| Overpayment percentage | 3-8% reported, actual 5-12% | prompt / analysis |
| Industrial generators with low CF | ~15% of settlements | settlements joined with nodes |
| Threshold-volume generators | ~8% of settlements | settlements where energy_mwh = 100 |
| Generators affected by both | ~2% of settlements | intersection (industrial + threshold) |
| Rate adjustments in period | Several, mixed statuses | rate_adjustments table |
| Meter firmware updates | ~30 generators | meter_firmware table |
| Transmission upgrades | 5 upgrades Oct-Jan | transmission_upgrades table |
| DECOMMISSIONED readings | Present but irrelevant | meter_readings quality_flag |
| Correct threshold comparison | >= (meets or exceeds) | README specification |
| Buggy threshold comparison | > (strictly greater) | loss_calculator.f90 |
| Correct rate tier logic | Check both location AND CF | README specification |
| Buggy rate tier logic | Location match skips CF | settlement_engine/app.py |

## Ideal Investigation Path

1. Query settlements to see total payouts and identify patterns
2. Query settlements summary endpoint to get aggregate statistics by type and zone
3. Query energy analysis endpoint to see settlement statistics by energy bucket — the 100-125 MWh bucket will show anomalously high unity_factor_count (loss_factor=1.0) compared to higher buckets, pinpointing the threshold boundary as a hotspot
4. Correlate with generator attributes through joins to nodes table
5. Notice patterns in rate_applied for industrial location generators
6. Notice patterns in loss_factor_applied for generators near 100 MWh — the energy analysis endpoint shows this directly
7. Cross-reference with rate_tiers to understand tier selection criteria
8. Cross-reference with loss_factors to understand threshold configuration
9. Analyze weather_data table and prove no relationship to settlement formula
10. Analyze transmission_upgrades table and prove no correlation with affected records
11. Analyze meter_firmware updates and prove no correlation with affected records
12. Analyze rate_adjustments and manual_adjustments tables and prove no correlation
13. Analyze meter reading quality_flag distributions and settlement_exceptions
14. Specifically investigate and dismiss DECOMMISSIONED quality flag theory from data quality team - query the `/api/settlements/data_quality_analysis` endpoint to compare overpayment metrics for generators with flagged readings vs clean-only readings by location type. This shows identical overpayment patterns in both groups, proving quality flags are not the cause
15. Read loss_calculator.f90 to find the boundary condition bug
16. Read settlement_engine/app.py to find the rate tier selection bug
17. Fix the Fortran boundary condition (> to >=)
18. Fix the Python rate tier selection (add capacity factor check)
19. Rebuild containers with fixes
20. Recalculate all settlements for affected periods
21. Verify recalculated values are correct

## Verification Queries

To verify the rate tier bug affects industrial generators:

```sql
SELECT g.name, g.generator_type, n.location_type, s.capacity_factor, s.rate_applied
FROM settlements s
JOIN generators g ON s.generator_id = g.id
JOIN nodes n ON g.location_id = n.id
WHERE n.location_type = 'industrial'
AND s.capacity_factor < 0.75
ORDER BY s.rate_applied DESC;
```

To verify the loss factor bug affects threshold-volume generators:

```sql
SELECT g.name, s.energy_mwh, s.loss_factor_applied
FROM settlements s
JOIN generators g ON s.generator_id = g.id
WHERE s.energy_mwh BETWEEN 99.9 AND 100.1
ORDER BY s.loss_factor_applied;
```
