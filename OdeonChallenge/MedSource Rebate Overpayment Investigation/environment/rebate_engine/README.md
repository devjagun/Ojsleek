# Rebate Calculation Engine

This service calculates quarterly rebate amounts for pharmacy customers based on their purchasing behavior and contract terms.

## Overview

The rebate engine processes customer order data and computes rebate payments using a three-stage calculation methodology developed by the Finance team in 2019. The core calculation logic runs through a compiled Ada binary for performance and numerical precision.

## Calculation Stages

### Stage 1: Volume Index

The volume index reflects purchasing performance relative to quarterly targets. Customers who exceed their target volume receive an enhanced index. Customers who fall short receive a reduced index. The surplus multiplier encourages volume growth while the deficit multiplier accounts for fixed costs.

### Stage 2: Product Mix Factor

The product mix factor adjusts for the composition of products purchased. Specialty product ratios affect the factor because specialty medications carry different margin profiles. Established pharmacy relationships also factor into the adjustment.

### Stage 3: Customer Class Rate

The customer class rate applies tiered multipliers based on certification status, volume levels, and contract terms. Different customer segments receive different rate structures based on their relationship with MedSource.

## API Endpoints

### GET /health

Returns service health status.

### POST /calculate

Calculates rebate for a single payment record.

Request body:
```json
{
  "payment_id": 1,
  "customer_id": 10,
  "quarterly_units": 45000,
  "quarterly_target": 40000,
  "specialty_ratio": 0.25,
  "certification_days": 200,
  "specialty_certified": true,
  "contract_tier": 2
}
```

### POST /batch-calculate

Processes all pending rebate payments in the database. Updates calculated_rebate values and creates audit log entries.

## Configuration

The service connects to PostgreSQL using environment variables:

- DB_HOST: Database hostname (default: postgres)
- DB_PORT: Database port (default: 5432)
- DB_NAME: Database name (default: medsource)
- DB_USER: Database user (default: medsource)
- DB_PASS: Database password

## Numerical Precision

All intermediate calculations follow specific rounding conventions established by Finance. Volume index rounds to two decimal places. Product mix factor rounds to three decimal places. Final rebate amounts round to two decimal places for payment processing.

## Troubleshooting

If rebate calculations seem incorrect, verify that input data matches expected formats. Certification days should be calculated from the certification grant date to the calculation date. Specialty ratio should be the proportion of specialty product units to total units for the quarter.

The audit log stores all calculation inputs and outputs for reconciliation purposes.
