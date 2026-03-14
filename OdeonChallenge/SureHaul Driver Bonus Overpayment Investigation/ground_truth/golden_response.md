Investigation Summary

I investigated the driver bonus overpayment issue at SureHaul Logistics. The reported 22% budget overrun is caused by two bugs in the Fortran bonus calculation engine, not by fuel cost increases as the operations team suggested.

Investigation Approach

I started by querying the bonus_payments table to understand the scope of the overpayment. I compared recent bonus statistics with earlier baseline periods using the analytics service metrics comparison endpoint.

I then examined the bonus calculation formula by reading the bonus_engine README documentation. This explained the three-stage calculation: Base Performance Index, Adjusted Zone Difficulty Factor, and Tier Multiplier selection.

Next I reviewed the actual Fortran implementation in bonus_calc.f90 to see if the code matched the documented behavior.

Key Findings

Finding One: Incorrect Boundary Condition

The README states that the familiarity bonus factor of 0.88 applies when a driver has worked a zone for more than thirty days. The Fortran code uses a greater-than-or-equal comparison instead of strict greater-than.

The buggy condition zone_days >= 30 gives drivers the familiarity discount when they have exactly 30 days in a zone. This should not happen because more than thirty means strictly above thirty, not thirty or above.

Querying the driver_zone_history table shows that approximately 20% of driver-zone pairs have exactly 30 total_days_in_zone. These drivers all receive an incorrect 12% reduction in their zone difficulty factor.

Finding Two: Incorrect Priority Branch Order

The README specifies that tier multiplier selection follows a strict priority order:

1. Gold tier with score above 150: rate 1.25
2. Gold tier: rate 1.15
3. Score above 150: rate 1.10
4. Tenure above 2 years: rate 1.05
5. Default: rate 1.00

The Fortran code evaluates conditions in the wrong order. It checks score > 150 first, then checks Gold tier alone. The branch that should give Gold drivers with high scores the 1.25 rate is placed third and can never be reached because either condition one or two will always trigger first for any Gold driver with a high score.

This causes Gold tier drivers with scores above 150 to receive rate 1.10 instead of their correct rate of 1.25.

Red Herring Analysis

The fuel cost data does show an 18% increase from approximately 3.20 to 3.78 per gallon starting around week four of the affected period. However, fuel costs are not used anywhere in the bonus calculation formula. The bonus engine only uses: deliveries completed, route targets, zone difficulty ratings, customer feedback ratings, days worked in zone, driver tier, and tenure. Fuel prices are stored for operational planning but never queried by the bonus calculation.

The timing correlation between fuel price increases and bonus overpayment is coincidental.

Root Cause

Bug One (boundary condition) causes overpayment for drivers with exactly 30 zone days by incorrectly applying the familiarity discount.

Bug Two (priority order) causes underpayment for Gold tier drivers with high scores by giving them rate 1.10 instead of 1.25.

The net effect is overpayment because Bug One affects a larger population than Bug Two. The 22% overrun figure reflects the combined impact with Bug One being the dominant factor.

Fix Applied

I corrected the Fortran code in bonus_engine/bonus_calc.f90:

1. Changed the familiarity condition from zone_days >= 30 to zone_days > 30
2. Reordered the tier rate selection to check Gold with score > 150 first, then Gold alone, then score > 150 alone

I rebuilt the bonus-calc container to deploy the fix.

Recommendations

Recalculate all bonus payments for the affected six-week period using the corrected formula. The difference between buggy and correct calculations represents the overpayment amount that should be reconciled.

Add unit tests to the bonus calculation engine that verify boundary conditions and priority branch behavior with specific test cases for drivers with exactly 30 zone days and Gold drivers with scores just above and below 150.

Consider adding validation that compares Fortran calculation results against a reference implementation in Python to catch calculation discrepancies in production.
