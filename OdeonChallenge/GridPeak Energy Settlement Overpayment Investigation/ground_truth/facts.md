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

## Expected Correct Values

After fixing both bugs, settlements should show:

- Average loss factors increase by approximately 0.02 to 0.04 for threshold-volume generators
- Industrial location generators with capacity factor below 0.75 see rate reductions of 10 to 25 percent
- Overall settlement overpayment correction of approximately five to twelve percent system-wide

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
