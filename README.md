# CRE Underwriting Automation

Automates commercial real estate underwriting - generates 10-year Excel cash flow models in seconds instead of days.

## Quick Start

```bash
# 1. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 2. Start API
cd backend
python api.py
# Runs at http://localhost:5001

# 3. Use web interface
# Open frontend/underwriting_interface.html in browser
```

## API Usage

**Endpoint:** `POST /underwrite`

```bash
curl -X POST http://localhost:5001/underwrite \
  -H "Content-Type: application/json" \
  -d '{
    "property_address": "120 Valleywood Drive",
    "tenant": "Sentrex Health Solutions Inc.",
    "area_sf": 60071,
    "current_rent_psf": 14.21,
    "lease_start": "3/1/2022",
    "lease_end": "2/29/2032",
    "annual_escalation": 3.0,
    "purchase_price": 17800000,
    "renewal_probability": 85,
    "market_rent_psf": 17.50,
    "market_escalation": 3.5,
    "vacancy_months": 8,
    "ti_psf": 5.0
  }' \
  --output underwriting.xlsx
```

## What It Does

- **Calculates** 10-year cash flow projections with rent escalations
- **Models** lease expiry scenarios (renewal probability)
- **Generates** Excel file with formulas (not static values!)
- **Includes** 4 worksheets:
  - Cash Flow (10-year projections)
  - Valuation Summary (IRR, NPV)
  - Rent Schedule (all escalations)
  - Market Leasing Assumptions

## Project Structure

```
├── backend/
│   ├── api.py              # Flask API (1 endpoint)
│   ├── cre_underwriter.py  # Financial engine
│   └── requirements.txt
├── frontend/
│   └── underwriting_interface.html  # Web UI
├── tests/                  # Test files
├── outputs/                # Generated Excel files
└── docs/                   # Documentation
```

## Everything is Dynamic

No templates! Every calculation uses your inputs. Change any parameter → all formulas recalculate.

See [PROOF_ITS_DYNAMIC.md](PROOF_ITS_DYNAMIC.md) for technical details.
