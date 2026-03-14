# MedSource Rebate Overpayment Investigation - Analysis Report

## Executive Summary

After investigating the rebate calculation system I found two bugs in the Ada calculation engine that together cause the overpayment issue. The total financial impact is approximately eight hundred forty seven thousand dollars for Q4.

## Investigation Approach

I started by reviewing the PRMS specification document to understand how rebates are supposed to be calculated. Then I examined the actual Ada code in the rebate engine to compare implementation against specification. I also reviewed the red herrings mentioned by other teams and confirmed they are not related to the root cause.

## Findings

### Root Cause One: Certification Duration Boundary Condition

The specification states that specialty certification must be active for MORE than one hundred eighty days to qualify for enhanced rates. The Ada code incorrectly uses a greater than or equal comparison instead of strictly greater than.

In the Calculate_Product_Mix_Factor function the code has:

Qualifies_Cert := (Cert_Days >= 180);

This should be:

Qualifies_Cert := (Cert_Days > 180);

This causes pharmacies certified for exactly one hundred eighty days to incorrectly receive enhanced rebate rates when they should not qualify yet.

### Root Cause Two: Additive Bonus Accumulation

The specification defines exclusive product mix factor rates where the compound rate of one point two eight should apply to pharmacies with both specialty certification and high volume. The code incorrectly treats these as additive bonuses.

The buggy code adds zero point one eight for specialty certification and zero point one two for high volume status. When both apply the result is one point three zero instead of the correct one point two eight. This two percent excess on high value accounts explains why the overpayment is concentrated among specialty certified high volume pharmacies.

## Red Herrings Dismissed

Hospital contracts: The hospital pricing module is completely separate from pharmacy rebate calculations. Different code paths and different tables.

Seasonal factors: Seasonal adjustment factors are used only for forecasting and reporting. They do not affect the core rebate calculation formula.

New specialty pharmacies: The three new onboarded pharmacies have correct tier assignments in the database. The bug affects all specialty pharmacies not just new ones.

Price list updates: Manufacturer price changes affect base pricing but the rebate calculation percentages and multipliers are independent of unit prices.

## Fix Applied

I modified the rebate_calc.adb file with two changes:

First I changed the certification duration comparison from greater than or equal to strictly greater than for the one hundred eighty day threshold.

Second I replaced the additive bonus logic with exclusive conditional checks. The compound condition for specialty plus high volume is now evaluated first and returns one point two eight. Specialty only returns one point one eight. High volume only returns one point one two. Otherwise the standard rate of one point zero zero applies.

## Verification

After applying the fix the verifier confirms both bugs are resolved and no fabricated modifications were made to wrapper files.

## Recommendations

One: Deploy the fixed rebate_calc.adb to production after standard testing.

Two: Recalculate Q4 rebates for affected pharmacy accounts and issue correction notices.

Three: Add unit tests for boundary conditions especially the one hundred eighty day certification threshold.

Four: Consider adding validation in the Python wrapper to catch calculation anomalies before payment processing.

Five: Document the exclusive nature of product mix factor rates more prominently in the specification to prevent future similar bugs.
