# How the CRE Underwriting Application Works

## Overview

Yes, this is a **real working financial engine** that performs commercial real estate underwriting calculations. It replicates what analysts manually do in Excel/Argus.

## The Financial Engine ([backend/cre_underwriter.py](backend/cre_underwriter.py))

### What It Actually Does:

**1. Cash Flow Modeling (Lines 121-355)**

The engine builds a year-by-year 10-year cash flow projection:

```python
# Year 1-6: In-place lease with 3% escalations
Base Rent: $853,609 → $879,217 → $905,594... (grows 3% annually)

# Year 7: Lease expires
- 85% probability: Tenant renews at market rent ($17.50/SF)
- 15% probability: 8 months vacancy + leasing costs

# Year 7-11: Market lease with 3.5% escalations
Market Rent: $1,051,243 → $1,088,036... (grows 3.5% annually)
```

**2. Real Formula Generation**

Instead of hardcoding numbers, it writes **actual Excel formulas**:

```python
# Example from line 186:
ws.cell(row, col).value = f'={prev_cell}*(1+{escalation_rate})'

# This creates: =B9*(1+0.03) in the Excel cell
# So when you change inputs in Excel, everything recalculates!
```

**3. Probability-Weighted Scenarios (Lines 196-215)**

Models lease expiry risk:

```python
# Vacancy calculation (line 207):
vacancy_factor = (vacancy_months / 12) * non_renewal_probability
# If 8 months and 15% non-renewal = 0.1 (10% of rent lost)

# Leasing costs only apply if tenant doesn't renew (line 307):
ws.cell(row, col).value = f'={noi_cell}*0.08*{non_renewal_prob}'
```

**4. Four Excel Worksheets**

- **Valuation Summary**: IRR, NPV, return metrics
- **Cash Flow**: 10-year monthly projections with formulas
- **Rent Schedule**: Every rent step with dates
- **Market Leasing**: All assumptions documented

## How the Frontend Works ([frontend/underwriting_interface.html](frontend/underwriting_interface.html))

### User Flow:

1. **User fills form** (lines 241-338)
   - Property details, lease terms, market assumptions
   - All pre-filled with example values

2. **JavaScript captures data** (lines 361-380)
   - Converts form fields to JSON
   - Formats dates, converts strings to numbers

3. **Sends to API** (line 388)
   ```javascript
   fetch('http://localhost:5001/underwrite/simple', {
       method: 'POST',
       body: JSON.stringify(data)
   })
   ```

4. **Backend processes** → **Returns Excel file** (lines 396-405)
   - Creates blob from response
   - Triggers browser download
   - Filename includes property name and date

## How the API Works ([backend/api.py](backend/api.py))

### Two Endpoints:

**1. Simple Endpoint** (lines 132-188)
```python
POST /underwrite/simple

Input: Broker-friendly format (rent PSF, percentages)
Output: Excel file download
```

**2. Full Endpoint** (lines 19-130)
```python
POST /underwrite

Input: Detailed JSON with all nested parameters
Output: Excel file download
```

## How to Customize Parameters

### Option 1: Edit the Web Form

Open [frontend/underwriting_interface.html](frontend/underwriting_interface.html):

```html
<!-- Line 253: Change default purchase price -->
<input type="number" id="purchase_price" value="17800000">

<!-- Line 309: Change default renewal probability -->
<input type="number" id="renewal_probability" value="85">

<!-- Line 335: Change default exit cap -->
<input type="number" id="exit_cap_rate" value="6.50">
```

### Option 2: Edit the Engine Defaults

Open [backend/cre_underwriter.py](backend/cre_underwriter.py):

```python
# Line 583-602: Change the example property data
assumptions = {
    'renewal_probability': 0.85,  # Change to 0.90 for 90%
    'market_rent_psf': 17.50,     # Change market rent
    'vacancy_months': 8,           # Change downtime
    'exit_cap_rate': 0.065,        # Change cap rate
    # Add more parameters...
}
```

### Option 3: API Call with Custom Values

```bash
curl -X POST http://localhost:5001/underwrite/simple \
  -H "Content-Type: application/json" \
  -d '{
    "purchase_price": 25000000,        # Your custom price
    "renewal_probability": 90,         # 90% renewal
    "market_rent_psf": 20.00,          # $20/SF market
    "vacancy_months": 6,               # 6 months downtime
    "ti_psf": 8,                       # $8/SF TI allowance
    ...
  }'
```

### Common Parameters to Adjust:

| Parameter | Location | What It Does |
|-----------|----------|--------------|
| `purchase_price` | Form/API | Property acquisition cost |
| `renewal_probability` | Form/API | % chance tenant stays (85 = 85%) |
| `market_rent_psf` | Form/API | Market rent upon lease expiry |
| `vacancy_months` | Form/API | Downtime if tenant leaves |
| `ti_psf` | Form/API | Tenant improvement allowance |
| `exit_cap_rate` | Form/API | Cap rate for resale value |
| `annual_escalation` | Form/API | In-place lease rent bumps |
| `market_escalation` | Form/API | Market lease rent bumps |

## The Math Behind It

### Example Calculation Flow:

**Input:**
- Property: $17.8M purchase
- Current rent: $14.21/SF × 60,071 SF = $853,609/year
- Lease expires: Year 7
- Renewal probability: 85%

**Year 1-6 (In-place lease):**
```
Year 1: $853,609
Year 2: $853,609 × 1.03 = $879,217
Year 3: $879,217 × 1.03 = $905,594
...
```

**Year 7 (Lease expiry - probability weighted):**
```
Renewal scenario (85%):
  New rent: $17.50/SF × 60,071 = $1,051,243

Non-renewal scenario (15%):
  Vacancy: 8 months = 66.7% of year lost
  Lost rent: $1,051,243 × 0.667 = -$701,329

Blended: $1,051,243 × 0.85 - $701,329 × 0.15 = $787,856
```

**Leasing Costs (Year 7):**
```
TI: $5/SF × 60,071 × 15% non-renewal = $45,053
Commission Y1: NOI × 8% × 15% = $9,463
Commission Y2: NOI × 3.5% × 15% = $4,287
```

**Result:** Professional Excel package with all formulas intact, ready for client review or further customization.

---

**The key advantage:** All calculations are transparent Excel formulas, not black box hardcoded values. Open the Excel file and see exactly how every number is calculated!
