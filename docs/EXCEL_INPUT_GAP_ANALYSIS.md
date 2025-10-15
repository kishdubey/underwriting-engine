# Excel Rent Roll Input - Gap Analysis

## What the Senior Broker Sends

### Current Excel Rent Roll Contains:

**Property Summary:**
- Property Address: 120 Valleywood Drive
- Unit Number: 00001
- Tenant: Sentrex Health Solutions Inc.
- Lease Type: Industrial Net Lease (NNN)
- Area: 60,071 SF
- Lease From: 03/01/2022
- Lease To: 02/29/2032
- Term: 120 months (10 years)
- Monthly Rent: $71,134.08
- Monthly Rent/Area: $1.18/SF
- Annual Rent: $853,608.91
- Annual Rent/Area: $14.21/SF
- CAM Recovery: $5.07/SF
- Tax Recovery: $2.17/SF
- Security Deposit: $140,581.38

**Rent Steps (Escalations):**
```
Date Range              Monthly    $/SF/Mo   Annual      $/SF/Year
03/01/2025-02/28/2026  $71,134    $1.18     $853,609    $14.21
03/01/2026-02/28/2027  $73,237    $1.21     $878,839    $14.63
03/01/2027-02/29/2028  $75,439    $1.25     $905,270    $15.07
03/01/2028-02/28/2029  $77,692    $1.29     $932,302    $15.52
03/01/2029-02/28/2030  $80,045    $1.33     $960,535    $15.99
03/01/2030-02/28/2031  $82,447    $1.37     $989,369    $16.47
03/01/2031-02/29/2032  $84,900    $1.41    $1,018,804   $16.96
```

**Recovery Schedules:**
- CAM: $304,829.40/year ($5.07/SF)
- Tax: $130,901.16/year ($2.17/SF)
- Share: 100% (single tenant)

---

## What Our Current System Captures

### API Input Fields:

```json
{
  "property_address": "120 Valleywood Drive",        ✓ FROM EXCEL
  "tenant": "Sentrex Health Solutions Inc.",         ✓ FROM EXCEL
  "area_sf": 60071,                                  ✓ FROM EXCEL
  "current_rent_psf": 14.21,                         ✓ FROM EXCEL
  "lease_start": "03/01/2022",                       ✓ FROM EXCEL
  "lease_end": "02/29/2032",                         ✓ FROM EXCEL
  "annual_escalation": 3.0,                          ✓ CALCULATED FROM RENT STEPS
  "purchase_price": 17800000,                        ✗ FROM EMAIL (not in Excel)
  "renewal_probability": 85,                         ✗ FROM EMAIL (not in Excel)
  "market_rent_psf": 17.50,                          ✗ FROM EMAIL (not in Excel)
  "market_escalation": 3.5,                          ✗ FROM EMAIL (not in Excel)
  "vacancy_months": 8,                               ✗ FROM EMAIL (not in Excel)
  "ti_psf": 5.0                                      ✗ FROM EMAIL (not in Excel)
}
```

---

## What We're Missing from Excel

### Currently NOT Captured:

1. **CAM Recoveries** ($5.07/SF = $304,829/year)
   - We ignore this completely
   - For NNN lease, this is tenant-paid operating expenses

2. **Tax Recoveries** ($2.17/SF = $130,901/year)
   - We ignore this completely
   - For NNN lease, tenant pays property taxes

3. **Security Deposit** ($140,581.38)
   - Not used in cash flow
   - Could be relevant for risk analysis

4. **Unit Number** (00001)
   - Not captured (only matters for multi-unit)

5. **Monthly Breakdown**
   - Excel has monthly, we only use annual

6. **Recovery Pool Details**
   - Share %, Management %, Cap, Base Year
   - Not relevant for single-tenant NNN

---

## Impact Analysis

### What We Calculate Correctly:

✅ **Base Rent Escalations**
- Excel shows: $853,609 → $878,839 → $905,270...
- We calculate: 3% escalation applied correctly
- **Status: CORRECT**

✅ **Current Rent PSF**
- Excel shows: $14.21/SF
- We use: $14.21/SF
- **Status: CORRECT**

✅ **Lease Dates**
- Excel shows: 03/01/2022 to 02/29/2032
- We use: Same dates
- **Status: CORRECT**

### What We're Missing:

❌ **CAM & Tax Recoveries**
- Excel shows: $5.07 + $2.17 = $7.24/SF in recoveries
- We show: $0 in recoveries
- **Impact:** Understating NOI by $435,730/year

❌ **Total Cash Flow to Owner**
- Excel includes: Base Rent + CAM + Tax = $14.21 + $7.24 = $21.45/SF
- We only show: Base Rent = $14.21/SF
- **Impact:** Missing ~34% of actual cash flow

---

## Why This Matters

### For NNN (Triple Net) Leases:

In a NNN lease:
- **Tenant pays:** Base Rent + CAM + Property Tax + Insurance
- **Owner receives:** All of the above
- **Owner's expenses:** Debt service, capital reserves

**Our current calculation:**
```
NOI = Base Rent Only = $853,609/year
```

**Should be:**
```
NOI = Base Rent + CAM + Tax
    = $853,609 + $304,829 + $130,901
    = $1,289,339/year
```

**Yield Impact:**
```
Current Calculation:
Yield = $853,609 / $17,800,000 = 4.80%

Correct Calculation:
Yield = $1,289,339 / $17,800,000 = 7.24%
```

**We're understating yield by 244 basis points!**

---

## What Needs to Change

### Option 1: Add CAM/Tax Inputs to API

```json
{
  "current_rent_psf": 14.21,
  "cam_psf": 5.07,              // NEW
  "tax_psf": 2.17,              // NEW
  "insurance_psf": 0.00         // NEW (if applicable)
}
```

### Option 2: Parse Excel Directly

Create endpoint to upload Excel rent roll:
```
POST /underwrite/from-excel
- Upload Excel file
- Parse rent roll automatically
- Extract all fields
- Generate underwriting
```

### Option 3: Combined Rent Input

```json
{
  "total_rent_psf": 21.45,      // All-in NNN rent
  "base_rent_psf": 14.21,       // Subset for escalation modeling
  "operating_expenses_psf": 7.24 // CAM + Tax
}
```

---

## Current System Workflow

### What Happens Now:

1. **Senior broker sends:**
   - Email with market assumptions
   - Excel file with rent roll

2. **Analyst manually:**
   - Reads Excel rent roll
   - Extracts: Property, Tenant, Area, Rent/SF, Dates
   - Reads email for: Purchase price, renewal prob, market assumptions
   - **MANUALLY ADDS:** CAM + Tax to base rent

3. **Our system:**
   - Only captures base rent from Excel
   - Ignores CAM/Tax completely
   - Generates underwriting with incomplete NOI

### What Should Happen:

1. **Senior broker sends:**
   - Email with market assumptions
   - Excel file with rent roll (or uploads to web form)

2. **System automatically:**
   - Parses Excel rent roll
   - Extracts ALL revenue streams (Base + CAM + Tax)
   - Combines with email assumptions
   - Generates complete underwriting

3. **No manual intervention needed**

---

## Recommended Fix Priority

### HIGH PRIORITY:
1. ✅ Add CAM/Tax inputs to API and web form
2. ✅ Include recoveries in NOI calculation
3. ✅ Update yield calculations

### MEDIUM PRIORITY:
4. Add Excel upload/parsing capability
5. Validate against actual rent roll numbers

### LOW PRIORITY:
6. Security deposit tracking
7. Multi-unit support
8. Monthly vs annual breakdown

---

## Next Steps

1. **Immediate:** Add `cam_psf` and `tax_psf` fields to API
2. **Update engine:** Include in NOI calculation
3. **Update web form:** Add CAM/Tax inputs
4. **Test:** Verify yields match broker expectations
5. **Future:** Build Excel parser for rent rolls

---

**Bottom Line:** We're currently only modeling 66% of the actual cash flow because we ignore operating expense recoveries. For NNN leases, this is critical data.
