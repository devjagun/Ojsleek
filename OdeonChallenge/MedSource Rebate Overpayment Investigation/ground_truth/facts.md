# MedSource Rebate Overpayment Investigation - Facts

## Bug Summary

There are **TWO BUGS** in the rebate calculation system, both located in the Ada rebate calculation engine (`rebate_engine/rebate_calc.adb`) in the `Calculate_Product_Mix_Factor` function.

---

## Bug 1: Boundary Condition Error in Certification Duration Check

**Location:** `rebate_engine/rebate_calc.adb`, line ~73

**Current (Buggy) Code:**
```ada
Qualifies_Cert := (Cert_Days >= 180);
```

**Expected (Correct) Code:**
```ada
Qualifies_Cert := (Cert_Days > 180);
```

**Impact:** Customers who have been specialty-certified for exactly 180 days are incorrectly receiving the enhanced rebate rate when they should not qualify. According to the PRMS specification (section 6.1), certification must be active for MORE than 180 days (i.e., at least 181 days) to qualify for enhanced rates.

**Financial Impact:** Overpayment to customers at exactly the 180-day certification mark.

---

## Bug 2: Accumulation Error in Product Mix Factor Calculation

**Location:** `rebate_engine/rebate_calc.adb`, lines ~82-88

**Current (Buggy) Code:**
```ada
if Has_Spec_Cert and Qualifies_Cert then
   Factor := Factor + 0.18;  -- Add specialty bonus
end if;

if Is_High_Volume then
   Factor := Factor + 0.12;  -- Add high volume bonus
end if;
```

**Expected (Correct) Code:**
```ada
-- Check compound condition FIRST (most specific)
if Has_Spec_Cert and Qualifies_Cert and Is_High_Volume then
   return 1.28;  -- Compound rate: Specialty + High Volume
elsif Has_Spec_Cert and Qualifies_Cert then
   return 1.18;  -- Specialty only
elsif Is_High_Volume then
   return 1.12;  -- High volume only
else
   return 1.00;  -- Standard
end if;
```

**Impact:** The buggy code treats the specialty certification bonus (+0.18) and high volume bonus (+0.12) as ADDITIVE factors rather than EXCLUSIVE tiers. When a customer qualifies for BOTH:

- **Buggy calculation:** 1.00 + 0.18 + 0.12 = **1.30**
- **Correct calculation:** Compound rate = **1.28**

This results in a 1.5% overpayment for every customer who qualifies for both specialty certification AND high volume status.

**Financial Impact:** Significant overpayment to high-value customers who have both qualifications.

---

## Combined Bug Effect

The two bugs compound to create the overpayment pattern described in the prompt:

1. **Bug 1** causes customers certified for exactly 180 days to incorrectly qualify for specialty bonuses
2. **Bug 2** causes customers with both specialty cert AND high volume to receive 1.30x instead of 1.28x

Together, this explains the finance team's observation that "customers with BOTH specialty certification AND high volume are getting rebates calculated as if they qualify for our highest tier (1.28x product mix factor), but the amounts are even higher than that tier should produce."

---

## Red Herrings

The following are mentioned in the prompt but are NOT the cause of the bugs:

1. **Hospital contracts** - Separate module, not involved in pharmacy rebate calculation
2. **Seasonal factors** - Used for reporting only, not in rebate calculation  
3. **New specialty pharmacies** - Data entry is correct; bug is in calculation logic
4. **Price list updates** - Applied correctly; not related to rebate multiplier calculation

---

## Verification Criteria

A correct solution must:

1. Fix the certification duration check to use `>` instead of `>=` for the 180-day threshold
2. Change the product mix factor calculation to use exclusive conditional logic instead of accumulation
3. NOT introduce changes to unrelated files (app.py wrapper, analytics service, gateway, etc.)
4. NOT fabricate additional bugs that don't exist

## Files That Should Be Modified

Only one file should be modified:
- `rebate_engine/rebate_calc.adb`

## Files That Should NOT Be Modified

- `rebate_engine/app.py` (Flask wrapper)
- `analytics/app.py` (Analytics service)
- `gateway/main.go` (Go gateway)
- `_seed_data/init.sql` (Database seed)
- Any other file
