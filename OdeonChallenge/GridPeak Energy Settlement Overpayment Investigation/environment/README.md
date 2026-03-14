# GridPeak Energy Markets Settlement System

This system handles settlement calculations for power generators in the GridPeak energy market.

## Architecture Overview

The settlement system consists of three main services working together to calculate accurate payments for electricity generation.

### Gateway Service

The Go-based API gateway provides a unified interface for querying market data, generator information, and settlement records. All external queries should go through this service.

### Settlement Engine

The Python-based settlement engine orchestrates the payment calculation process. It aggregates meter readings, determines applicable rates, and computes final payment amounts.

### Loss Calculator

The Fortran-based loss calculator handles transmission loss computations. This legacy system has been in production for over fifteen years and provides highly accurate loss factor calculations based on zone characteristics and energy volumes.

## Settlement Process

Settlements are calculated weekly for each active generator. The process follows these steps:

First, meter readings are aggregated for the settlement period. Readings are recorded at fifteen minute intervals and converted to megawatt hours.

Second, the capacity factor is computed by dividing actual generation by theoretical maximum generation for the period.

Third, the appropriate rate tier is selected based on generator characteristics.

Fourth, gross payment is calculated by multiplying energy by the applicable rate.

Fifth, loss deductions are applied based on the loss factor returned by the loss calculator.

Sixth, congestion credits are added based on the node congestion factor.

Finally, the net payment is computed as gross payment minus loss deduction plus congestion credit.

## Rate Tier Selection

Rate tiers determine the price per megawatt hour paid to generators. Each generator type has multiple tiers with different qualifications.

The selection process evaluates tiers in priority order. Evaluate each tier starting from priority one. For each tier, check if the generator meets all specified criteria. The first tier where all criteria match determines the rate.

Tier criteria may include minimum capacity factor thresholds and location type requirements. If a criterion field is null, that criterion is not required for the tier. When both location_type and capacity factor criteria exist, both conditions must be satisfied for the tier to apply.

## Loss Factor Calculation

Transmission losses occur when electricity travels through the grid. The loss calculator determines an appropriate loss factor based on zone and energy volume.

Loss factors are applied based on energy delivery volumes relative to the configured threshold for each zone. The threshold boundary determines when the higher loss rate calculation applies.

The base loss factor starts at one point zero. When the threshold condition is satisfied, the zone-specific loss rate is added after applying the zone adjustment multiplier.

Additional tiered adjustments may apply for high volume deliveries. Volumes exceeding five hundred megawatt hours receive a bonus adjustment. Volumes exceeding one thousand megawatt hours receive an additional bonus.

The final factor is truncated to four decimal places.

## Data Model

### Generators

Each generator has a type, capacity in megawatts, and is associated with a grid node. Generator types include solar, wind, natural gas, coal, hydro, and nuclear. Some generators may have historical decommissioned dates.

### Nodes

Grid nodes represent connection points on the transmission network. Each node belongs to a zone and has a location type classification. The congestion factor indicates typical congestion levels at that node. Legacy code fields exist for historical tracking purposes.

### Rate Adjustments

Rate adjustments are submitted requests for payment modifications based on special circumstances. Only approved adjustments with valid effective dates are applied to settlements.

### Manual Adjustments

Manual adjustments track one-time payment corrections submitted by operators. Adjustments may be approved, rejected, voided, or pending review. Only adjustments with APPLIED status affect actual payments.

### Meter Readings

Meter readings capture actual power generation at fifteen minute intervals. Energy is measured in megawatts for the interval. Quality flags indicate readings that may have data quality concerns.

### Settlements

Settlement records store the calculated payment details for each generator and period. Records include the energy delivered, gross payment, loss deduction, congestion credit, and net payment.

### Settlement Exceptions

Settlement exceptions document periods with abnormal conditions that may affect payment calculations. Exception records track the affected zones, time periods, and payment impact percentages.

## Troubleshooting

### Incorrect Settlement Amountsabove or at the threshold. If factors appear unexpected, check:

The energy threshold configuration for the zone. The threshold boundary affects when higher rates apply.

The zone assignment for the generator node. Mismatched zones will use wrong loss parameters.

Recent transmission upgrades that may have affected grid topology.

Weather-related demand factor variations that could correlate with settlement anomalies.

### Rate Selection Problems

If generators receive unexpected rates, review the tier priority order. Tiers are evaluated sequentially and the first match wins. A generator may match an earlier tier before reaching the intended tier.

Check for any pending rate adjustments that may affect calculations. Only approved adjustments are applied.

Verify manual adjustment records for the affected generators. Voided or rejected adjustments should not impact settlements.

The capacity factor calculation uses the generators rated capacity. If capacity data is wrong, the calculated factor will be incorrect.

### Data Quality Concerns

Some meter readings may have quality flags indicating interpolated or estimated values. Review the quality_flag column for affected readings.

Orphaned meter readings (referencing decommissioned generators) should be excluded from settlement calculations.

Check for firmware update records around anomaly periods. Meter calibration changes may affect reading accuracy

Loss factors should be greater than one for deliveries meeting the threshold. If factors appear too low, check:

The energy threshold configuration for the zone. Deliveries must meet or exceed this value for the higher loss rate to apply.

The zone assignment for the generator node. Mismatched zones will use wrong loss parameters.

### Rate Selection Problems

If generators receive unexpected rates, review the tier priority order. Tiers are evaluated sequentially and the first match wins. A generator may match an earlier tier before reaching the intended tier.

The capacity factor calculation uses the generators rated capacity. If capacity data is wrong, the calculated factor will be incorrect.
