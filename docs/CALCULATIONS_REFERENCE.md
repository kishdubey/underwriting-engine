# CRE Underwriting - Complete Calculations Reference

This document explains every calculation and formula used in the underwriting engine.

---

## Table of Contents
1. [Input Parameters](#input-parameters)
2. [Cash Flow Calculations](#cash-flow-calculations)
3. [Rent Schedule](#rent-schedule)
4. [Leasing Costs](#leasing-costs)
5. [Valuation Metrics](#valuation-metrics)
6. [Excel Formula Examples](#excel-formula-examples)

---

## Input Parameters

### Property Data
```
Property Name        : User-provided string
Address              : User-provided string
Purchase Price (PP)  : Dollar amount (e.g., $17,800,000)
Property Type        : Industrial / Office / Retail
```

### Lease Data
```
Tenant Name          : User-provided string
Lease Start Date     : MM/DD/YYYY format
Lease End Date       : MM/DD/YYYY format
Lease Term           : Calculated = (End Date - Start Date) / 365.25
Current Annual Rent  : Calculated = Area (SF) × Rent PSF
Area (SF)            : Square footage (e.g., 60,071)
Escalation Rate      : Decimal (e.g., 0.03 = 3%)
```

### Market Assumptions (Upon Lease Expiry)
```
Renewal Probability      : Decimal (e.g., 0.85 = 85%)
Market Rent PSF          : Dollar per SF per year
Market Escalation Rate   : Decimal (e.g., 0.035 = 3.5%)
Market Term              : Years (default: 5)
Vacancy Months           : Number of months if non-renewal
TI PSF                   : Tenant improvements $ per SF
Exit Cap Rate            : Decimal (e.g., 0.065 = 6.5%)
```

### Financial Assumptions (Defaults)
```
Discount Rate            : 0.08 (8%)
Resale Rate              : 0.08 (8%)
Leveraged CF Rate        : 0.08 (8%)
Leveraged Resale Rate    : 0.08 (8%)
Hold Period              : 10 years
Selling Costs            : 0.00 (0%)
Leasing Commission Y1    : 0.08 (8% of NOI)
Leasing Commission Y2+   : 0.035 (3.5% of NOI)
```

---

## Cash Flow Calculations

### Year 1 through Lease Expiry (In-Place Lease)

**Year 1 Rent:**
```
Base Rent (Year 1) = Current Annual Rent
                   = Area (SF) × Current Rent PSF
```

**Year 2+ Rent (before expiry):**
```
Excel Formula: =PreviousYear × (1 + Escalation Rate)

Example:
Year 1: $1,000,000
Year 2: =B10*(1+0.03)  → $1,030,000
Year 3: =C10*(1+0.03)  → $1,060,900
```

**Implementation (Python):**
```python
# Line 174-181 in cre_underwriter.py
if year == 1:
    ws.cell(row, col).value = base_rent
else:
    prev_cell = get_column_letter(col - 1) + str(row)
    if year <= lease_end_year:
        ws.cell(row, col).value = f'={prev_cell}*(1+{escalation_rate})'
```

### Lease Expiry Year (Probability-Weighted)

**Scenario 1 - Tenant Renews (Renewal Probability %):**
```
New Rent = Area (SF) × Market Rent PSF
```

**Scenario 2 - Tenant Leaves (1 - Renewal Probability):**
```
Vacancy Period = Vacancy Months / 12
Lost Rent = New Rent × Vacancy Period
```

**Vacancy Calculation:**
```
Excel Formula: =-AnnualRent × (VacancyMonths/12) × NonRenewalProb

Example (8 months, 15% non-renewal):
Vacancy Factor = (8/12) × 0.15 = 0.10
Vacancy Loss = -$1,051,243 × 0.10 = -$105,124
```

**Implementation (Python):**
```python
# Line 196-215 in cre_underwriter.py
vacancy_year = lease_end_year + 1
vacancy_months = assumptions['vacancy_months']
non_renewal_prob = 1 - assumptions['renewal_probability']

if year == vacancy_year:
    annual_rent_cell = get_column_letter(col) + str(row - 1)
    vacancy_factor = (vacancy_months / 12) * non_renewal_prob
    ws.cell(row, col).value = f'=-{annual_rent_cell}*{vacancy_factor}'
else:
    ws.cell(row, col).value = 0
```

### Post-Expiry Rent (Market Lease)

**First Year After Expiry:**
```
Market Rent = Area (SF) × Market Rent PSF
```

**Subsequent Years:**
```
Excel Formula: =PreviousYear × (1 + Market Escalation Rate)

Example (3.5% market escalation):
Year 11: $1,200,000
Year 12: =K10*(1+0.035)  → $1,242,000
Year 13: =L10*(1+0.035)  → $1,285,470
```

**Implementation (Python):**
```python
# Line 185-188 in cre_underwriter.py
if year == lease_end_year + 1:
    market_rent = assumptions['market_rent_psf'] * area
    ws.cell(row, col).value = market_rent
else:
    ws.cell(row, col).value = f'={prev_cell}*(1+{assumptions["market_escalation_rate"]})'
```

---

## Leasing Costs

### Tenant Improvements (TI)

**Occurs in:** Year of lease expiry (non-renewal scenario only)

```
TI Cost = Area (SF) × TI PSF × Non-Renewal Probability

Excel Formula: =Area × TI_PSF × (1 - RenewalProb)

Example:
Area: 60,071 SF
TI: $5/SF
Non-Renewal: 15%

TI Cost = 60,071 × $5 × 0.15 = $45,053
```

**Implementation (Python):**
```python
# Line 286-297 in cre_underwriter.py
ti_year = vacancy_year
ti_psf = assumptions['tenant_improvements_psf']

if year == ti_year:
    ws.cell(row, col).value = ti_psf * area * non_renewal_prob
else:
    ws.cell(row, col).value = 0
```

### Leasing Commissions

**Year 1 Commission (8% of NOI):**
```
Excel Formula: =NOI × 0.08 × Non-Renewal Probability

Example:
NOI: $1,200,000
Non-Renewal: 15%

Commission Y1 = $1,200,000 × 0.08 × 0.15 = $14,400
```

**Year 2+ Commission (3.5% of NOI):**
```
Excel Formula: =NOI × 0.035 × Non-Renewal Probability

Commission Y2 = $1,200,000 × 0.035 × 0.15 = $6,300
```

**Implementation (Python):**
```python
# Line 299-316 in cre_underwriter.py
lc_year = vacancy_year

if year == lc_year:
    # 8% of Year 1 NOI
    noi_cell = get_column_letter(col) + str(noi_row)
    ws.cell(row, col).value = f'={noi_cell}*0.08*{non_renewal_prob}'
elif year == lc_year + 1:
    # 3.5% of Year 2 NOI
    noi_cell = get_column_letter(col) + str(noi_row)
    ws.cell(row, col).value = f'={noi_cell}*0.035*{non_renewal_prob}'
else:
    ws.cell(row, col).value = 0
```

### Total Leasing & Capital Costs

```
Total L&C = Tenant Improvements + Leasing Commissions

Excel Formula: =SUM(TI_Row:LC_Row)
```

---

## Revenue & Income Calculations

### Scheduled Base Rent
```
Excel Formula: =SUM(Potential Base Rent + Vacancy)

Note: Vacancy is negative, so this nets out the vacancy loss
```

### Effective Gross Revenue (EGR)
```
For NNN (Triple Net) Lease:
EGR = Scheduled Base Rent

(No operating expenses recovered from tenant)
```

### Net Operating Income (NOI)
```
For NNN Lease:
NOI = EGR - Operating Expenses
    = EGR - 0  (tenant pays all expenses)
    = EGR

Excel Formula: =EGR_Cell
```

### Cash Flow Before Debt Service
```
CFBDS = NOI - Leasing & Capital Costs

Excel Formula: =NOI_Cell - Capital_Costs_Cell
```

### Cash Flow Available for Distribution
```
For Unleveraged (no debt):
CFAD = CFBDS

Excel Formula: =CFBDS_Cell
```

---

## Valuation Metrics

### Yield on Purchase Price

```
Yield (Year N) = NOI (Year N) / Purchase Price

Excel Formula: =NOI_Cell / PurchasePrice

Example:
Year 1 NOI: $1,000,000
Purchase Price: $15,000,000

Yield = $1,000,000 / $15,000,000 = 6.67%
```

**Implementation (Python):**
```python
# Line 269-277 in cre_underwriter.py
ws[f'A{row}'] = f'Yield on PP (${property_data["purchase_price"]/1000000:.2f}M)'
pp = property_data['purchase_price']

for col in range(2, 14):
    if col <= 12:  # Not for total column
        ws.cell(row, col).value = f'={get_column_letter(col)}{noi_row}/{pp}'
        ws.cell(row, col).number_format = '0.00%'
```

### Net Present Value (NPV)

```
NPV = Sum of PV(Cash Flows) - Initial Investment

PV(CF) = CF / (1 + Discount Rate)^Year

Example:
Year 1 CF: $1,000,000, Discount Rate: 8%
PV(Year 1) = $1,000,000 / (1.08)^1 = $925,926
```

### Internal Rate of Return (IRR)

```
IRR = Rate where NPV = 0

Solve for r:
0 = -Initial Investment + CF1/(1+r)^1 + CF2/(1+r)^2 + ... + CFn/(1+r)^n
```

### Exit Value (Residual Sale)

```
Year 10 NOI = Net Operating Income in Year 10
Exit Value = Year 10 NOI / Exit Cap Rate

Excel Formula: =NOI_Year10 / ExitCapRate

Example:
Year 10 NOI: $1,300,000
Exit Cap: 6.5%

Exit Value = $1,300,000 / 0.065 = $20,000,000
```

---

## Rent Schedule Formulas

### Date Progression

```
Next Escalation Date = Previous Date + 1 Year

Python:
current_date = start_date + relativedelta(years=year)
```

### Rent After Escalation

```
New Rent = Previous Rent × (1 + Escalation Rate)

Python:
annual_rent *= (1 + lease_data['escalation_rate'])
```

### Rent Per SF

```
Rate/Area = Annual Rent / Area (SF)

Example:
Annual Rent: $1,025,000
Area: 50,000 SF

Rate = $1,025,000 / 50,000 = $20.50/SF
```

**Implementation (Python):**
```python
# Line 400-417 in cre_underwriter.py
for year in range(1, lease_data['lease_term_years']):
    current_date = start_date + relativedelta(years=year)
    annual_rent *= (1 + lease_data['escalation_rate'])
    rate_per_sf = annual_rent / area

    ws.cell(row, 1).value = current_date.strftime('%m/%d/%Y')
    ws.cell(row, 7).value = annual_rent
    ws.cell(row, 8).value = rate_per_sf
```

### Vacancy Period

```
Vacancy Start = Lease End Date + 1 Month
Vacancy End = Lease End Date + Vacancy Months

Python:
vacancy_end = lease_end + relativedelta(months=assumptions['vacancy_months'])
```

### Market Lease Start

```
Market Start Date = Vacancy End Date + 1 Month

Python:
market_start = vacancy_end + relativedelta(months=1)
```

---

## Excel Formula Examples

### Cash Flow Sheet

**Cell B10 (Year 1 Rent):**
```
Value: 1000000
```

**Cell C10 (Year 2 Rent):**
```
Formula: =B10*(1+0.025)
Result: 1025000
```

**Cell K10 (Year 10 Rent - After Expiry):**
```
Value: 1200000  (Market rent)
```

**Cell L10 (Year 11 Rent):**
```
Formula: =K10*(1+0.03)
Result: 1236000
```

**Cell K11 (Year 10 Vacancy):**
```
Formula: =-K10*0.15
Result: -180000
(9 months / 12 months × 20% non-renewal)
```

**Cell B21 (Year 1 NOI):**
```
Formula: =B18
(References Effective Gross Revenue)
```

**Cell B22 (Year 1 Yield):**
```
Formula: =B21/15000000
Result: 0.0667  (6.67%)
Format: 0.00%
```

**Cell K25 (Year 10 TI):**
```
Value: 80000
Calculation: 50000 SF × $8/SF × 0.20
```

**Cell K26 (Year 10 Leasing Commission):**
```
Formula: =K21*0.08*0.2
Calculation: NOI × 8% × 20% non-renewal
```

**Cell L26 (Year 11 Leasing Commission):**
```
Formula: =L21*0.035*0.2
Calculation: NOI × 3.5% × 20% non-renewal
```

**Cell B30 (Year 1 Cash Flow):**
```
Formula: =B21-B28
Calculation: NOI - Capital Costs
```

---

## Summary of Key Formulas

| Metric | Formula |
|--------|---------|
| Annual Rent | `Area (SF) × Rent PSF` |
| Escalated Rent | `Previous Rent × (1 + Escalation %)` |
| Vacancy Loss | `-Annual Rent × (Vacancy Months/12) × Non-Renewal %` |
| TI Cost | `Area × TI PSF × Non-Renewal %` |
| LC Year 1 | `NOI × 8% × Non-Renewal %` |
| LC Year 2+ | `NOI × 3.5% × Non-Renewal %` |
| NOI | `Rental Revenue - Operating Expenses` |
| Cash Flow | `NOI - Leasing & Capital Costs` |
| Yield | `NOI / Purchase Price` |
| Exit Value | `Final Year NOI / Exit Cap Rate` |
| NPV | `Σ(CF/(1+r)^t) - Initial Investment` |

---

## Code References

All calculations implemented in [backend/cre_underwriter.py](backend/cre_underwriter.py):

- **Cash Flow Modeling:** Lines 121-355
- **Rent Schedule:** Lines 356-481
- **Vacancy Calculations:** Lines 196-215
- **Leasing Costs:** Lines 282-334
- **Yield Calculations:** Lines 269-277
- **Market Rent:** Lines 185-188

---

## Formula Color Coding in Excel

**Blue Text:** User inputs (manually entered values)
**Black Text:** Calculated formulas
**Green Text:** Cross-sheet references

This follows industry-standard Excel modeling conventions for transparency and auditability.

---

*Last Updated: 2025-10-15*
