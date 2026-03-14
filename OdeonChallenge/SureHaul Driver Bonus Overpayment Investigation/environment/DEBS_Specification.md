# Driver Efficiency Bonus Score (DEBS) Specification

**Document Version:** 2.1  
**Last Updated:** January 2024  
**Owner:** Payroll Operations

This document describes the intended behavior of the Driver Efficiency Bonus Score calculation system. The calculation engine was developed by Operations Analytics and consists of three stages.

## Stage 1: Base Performance Index (BPI)

The BPI reflects delivery performance relative to route targets.

**Calculation:**
- Start with the route target as the base
- If deliveries exceed target: add the surplus multiplied by 1.15
- If deliveries fall short of target: subtract the deficit multiplied by 0.85

**Example:**
- Target: 30 deliveries, Completed: 35
- BPI = 30 + (5 × 1.15) = 35.75

**Example (underperformance):**
- Target: 30 deliveries, Completed: 25
- BPI = 30 + (-5 × 0.85) = 25.75

## Stage 2: Zone Difficulty Factor

The zone factor adjusts for zone characteristics and driver experience.

**Components:**

### Rating Adjustment Factor
- Drivers with customer rating exceeding 4.2 receive factor 0.92 (reduces bonus as top-rated drivers already receive higher base pay)
- All other drivers receive factor 1.0

### Zone Familiarity Factor  
- Drivers with more than thirty days experience in a zone receive factor 0.88 (familiar routes are easier)
- Drivers with thirty days or fewer receive factor 1.0

**The zone difficulty factor is:** base_difficulty × rating_factor × familiarity_factor

## Stage 3: Tier Rate Multiplier

The tier rate rewards tenure and performance excellence.

**Priority order (first matching condition applies):**

1. Gold tier AND performance score exceeds 150: rate 1.25
2. Gold tier (any score): rate 1.15  
3. Performance score exceeds 150: rate 1.10
4. Tenure exceeds 2 years: rate 1.05
5. Default: rate 1.00

**Note:** The compound condition (Gold AND high score) must be evaluated before individual conditions.

## Final Bonus Calculation

Final Bonus = BPI × Zone Difficulty Factor × Tier Rate

## Data Sources

| Input | Database Table | Column |
|-------|---------------|--------|
| Deliveries completed | shifts | deliveries_completed |
| Route target | shifts | route_target |
| Customer rating | feedback (aggregated) | rating |
| Zone days | driver_zone_history | total_days_in_zone |
| Driver tier | drivers | tier |
| Hire date | drivers | hire_date |
| Zone base difficulty | zones | base_difficulty |
