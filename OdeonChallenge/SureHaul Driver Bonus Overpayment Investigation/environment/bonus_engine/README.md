Bonus Calculation Engine

This service computes driver performance bonuses using our proprietary Driver Efficiency Bonus Score system developed by Operations Analytics in 2019. The core calculation engine is written in Fortran for numerical precision and performance.

For detailed formula specifications, see the DEBS_Specification.md file in the project root directory. The specification describes the intended calculation behavior across all three stages (BPI, Zone Factor, Tier Rate).

Architecture

The Fortran calculation engine receives input parameters via standard input and returns results via standard output. A Python Flask wrapper provides the REST API interface and handles database operations.

The binary was originally compiled by the Operations Analytics team but their documentation is no longer maintained after the team restructure in 2024. The current build process recompiles from source on container startup.

Configuration

The service connects to PostgreSQL using the DATABASE_URL environment variable. Default connection string is postgres://surehaul:surehaul123@postgres:5432/surehaul.

The Fortran binary is compiled at container build time and installed at /app/bonus_calc.

API Endpoints

GET /calculate/{driver_id}
Query parameters: period_start, period_end
Returns bonus calculations for all shifts in the specified period.

GET /scores/{driver_id}/breakdown
Query parameters: shift_date
Returns detailed breakdown for a specific shift bonus.

POST /batch-calculate
Body: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}
Recalculates and stores bonuses for all active drivers in the date range.

Troubleshooting

If the calculation engine returns no output, check that input values are properly formatted. The engine exits with code 1 on input parsing errors.

Contact payroll@surehaul.internal for calculation discrepancies. The analytics team maintains monitoring dashboards at grafana.surehaul.internal/d/bonus-calc.
