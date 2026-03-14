Root Cause

The bonus overpayment is caused by two bugs in the Fortran bonus calculation engine located in bonus_engine/bonus_calc.f90. The code is obfuscated with single-letter variable names making visual inspection difficult.

Bug One: Incorrect Boundary Condition for Familiarity Bonus

In the cz function (calculate zone difficulty), the condition for applying the familiarity bonus factor uses >= 30 when it should use > 30. The business rule is that familiarity bonus applies when a driver has worked more than thirty days in a zone.

Buggy code: if (zd >= 30) then
Correct code: if (zd > 30) then

This causes drivers with exactly 30 days in a zone to incorrectly receive the 0.88 familiarity factor, reducing their zone difficulty and increasing their final bonus.

Bug Two: Incorrect Priority Branch Order for Tier Multiplier

In the gr function (get rate), the conditional branches are in the wrong order. The correct business priority is:

1. Gold tier AND score exceeds 150: rate 1.25
2. Gold tier: rate 1.15
3. Score exceeds 150: rate 1.10
4. Tenure exceeds 2 years: rate 1.05
5. Default: rate 1.00

The buggy code checks score > 150 first, then checks Gold tier alone second. This means Gold tier drivers with scores above 150 receive rate 1.10 instead of rate 1.25, and the third branch checking both conditions together can never be reached.

Combined Effect

The two bugs have opposite effects but do not cancel out. Bug One overpays by giving undeserved familiarity discounts. Bug Two underpays some Gold tier high performers. The net effect is overpayment because Bug One affects a larger population.

Red Herrings

Red Herring One: Fuel Cost Increase

The prompt mentions operations team blaming fuel costs that increased 18% last month. The fuel_costs table shows a price increase from approximately 3.20 to 3.78 per gallon starting in early February.

Why it looks plausible: The timing correlates with the bonus overpayment period.

Why it falls apart: Fuel costs are not used anywhere in the bonus calculation. The calculation uses deliveries, targets, zone difficulty, ratings, zone days, tier, and tenure. Fuel prices are stored for operational planning but never queried by the bonus engine.

Red Herring Two: Training Program

The prompt mentions HR theory about a training program rolled out in late January.

Why it looks plausible: There is a training_completions table showing completions in January/February. Some affected drivers did complete training recently.

Why it falls apart: Training completion is not a variable in bonus calculations. The affected population does not correlate with training completion when analyzed statistically. Many non-trained drivers are also affected.

Red Herring Three: Vehicle Type Changes

The prompt mentions zone managers blaming new Sprinter vehicles in the North region.

Why it looks plausible: The vehicle_assignments table shows various vehicle types including Sprinters. Some affected drivers do have Sprinter assignments.

Why it falls apart: Vehicle type is not used in bonus calculations. The affected population spans all vehicle types proportionally. Sprinter assignments do not correlate with overpayment when controlled for other factors.

Red Herring Four: Zone Manager Changes

The zone_managers table shows some management transitions during the affected period.

Why it looks plausible: Leadership changes sometimes cause process variations.

Why it falls apart: Zone manager is not a variable in bonus calculations. Manager changes do not align with the affected driver population. The bugs are in code, not in management policy.

Red Herring Five: Batch Processing Issues

The calc_audit_log table contains some records that might look like duplicates or errors.

Why it looks plausible: IT mentioned seeing anomalies in logs.

Why it falls apart: The audit logs show normal operation. No actual duplicate payments exist. The bug is in calculation logic, not in payment processing.

Key Metrics

| Metric | Value | Source |
|--------|-------|--------|
| Overpayment percentage | 22% | prompt |
| Drivers with exactly 30 zone days | ~25% of driver-zone pairs | driver_zone_history table |
| Gold tier drivers | 15% of drivers | drivers table |
| Gold drivers with score > 150 | ~5% of all shifts | bonus_payments table |
| Fuel price increase | 18% | fuel_costs table |
| Correct familiarity threshold | > 30 days | Business rule |
| Buggy familiarity threshold | >= 30 days | bonus_calc.f90 cz function |
| Correct Gold high-score rate | 1.25 | Business rule |
| Buggy Gold high-score rate | 1.10 | bonus_calc.f90 gr function |

Ideal Investigation Path

1. Query bonus_payments to see total payouts and identify patterns
2. Query analytics service endpoints to get bonus summary statistics
3. Correlate with driver attributes through joins
4. Notice patterns in zone_difficulty_factor and tier_multiplier columns
5. Cross-reference with driver_zone_history to find 30-day boundary cases
6. Cross-reference with drivers table to find Gold tier high performers
7. Analyze fuel_costs table and prove no relationship to bonus formula
8. Analyze training_completions and prove no correlation with affected records
9. Analyze vehicle_assignments and prove no correlation with affected records
10. Analyze zone_managers and prove no correlation with affected records
11. Read bonus_calc.f90 to find the actual calculation logic (obfuscated)
12. Identify the boundary condition bug in cz function
13. Identify the priority branch bug in gr function
14. Fix the Fortran code
15. Rebuild the bonus-calc container
16. Verify calculations are now correct
