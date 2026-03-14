### AI Trip Traps (Use Where Applicable)
```markdown
# Prefer combining multiple traps in one challenge section so one mistake cascades across outputs.

1) Stateful row-order dependency:
Current row result depends on previous computed row result (not only raw input values).

2) Intermediate rounding trap:
Round or truncate intermediate values before later operations, and state exact stage + precision.

3) Boundary trap:
Explicit inclusive/exclusive boundaries (>= vs >, within N days including day N or not).

4) Priority branch trap:
5+ mutually exclusive conditional branches with strict evaluation order.

5) Conditional join trap:
Different lookup strategy by record type (exact match vs fallback to previous effective row).

6) Context null trap:
Null handling differs by column and status context (zero, carry-forward, drop, or default).

7) Temporal alignment trap:
Align records across periods/ranges (effective-from/effective-to, quarter mapping, business-day logic).

8) Exclusion-rule trap:
Different filters per metric family (count metrics vs financial metrics vs ratio metrics).

9) Cross-output consistency trap:
Same threshold/filter must produce consistent behavior in two output artifacts.

10) Double-cap trap:
Use min/max with two independent caps so implementing only one cap fails key scenarios.
```

### Rounding Trap Rules (High Priority)
```markdown
- Do not rely on final-output-only rounding when business logic requires staged rounding.
- If rounding is required, README must state where each stage happens and the precision/type (round vs truncate).
- Tests must verify staged rounding behavior with exact expected values.
- Avoid fragile wall-clock performance checks; prefer deterministic behavioral checks.
```