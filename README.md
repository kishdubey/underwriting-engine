# CRE Underwriting Engine

Automated commercial real estate underwriting that generates 10-year Excel cash flow models in 10 seconds instead of 5 days.

## Quick Start

```bash
# 1. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 2. Start API
cd backend
python api.py
# API runs at http://localhost:5001

# 3. Use Web Interface
Open frontend/underwriting_interface.html in your browser
```

## Features

- **10-second generation** - Instant vs 5-day manual process
- **Dynamic Excel formulas** - Not static templates
- **Complete financial modeling** - Cash flows, IRR, NPV, yields
- **Probability-weighted scenarios** - Lease expiry risk modeling
- **REST API + Web UI** - Easy integration
- **Production-ready** - For single-tenant properties

## API Usage

```bash
curl -X POST http://localhost:5001/underwrite \
  -H "Content-Type: application/json" \
  -d @examples/sample_request.json \
  --output underwriting.xlsx
```

**Generates Excel with:**
- Cash Flow (10-year projections)
- Valuation Summary (IRR, NPV, yields)
- Rent Schedule (all escalations)
- Market Leasing Assumptions

## Project Structure

```
underwriting_mvp/
├── backend/
│   ├── api.py                  # Flask REST API
│   ├── cre_underwriter.py      # Financial engine
│   └── requirements.txt        # Python dependencies
├── frontend/
│   └── underwriting_interface.html  # Web UI
├── tests/
│   ├── test_api.py            # API tests
│   └── test_underwriter.py    # Engine tests
├── examples/
│   └── sample_request.json    # Example API request
├── outputs/                   # Generated Excel files
└── Documentation (see below)
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for complete file layout.

## How It Works

1. **Input:** Property details, lease terms, market assumptions
2. **Engine:** Calculates 10-year cash flow with formulas
3. **Output:** Professional Excel file with 4 worksheets

**Key Calculation:** Cash flow starts with current rent (after applying escalations from lease start to analysis start date), not original base rent.

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 3-step setup guide
- **[CALCULATIONS_REFERENCE.md](CALCULATIONS_REFERENCE.md)** - Every formula explained
- **[HOW_IT_WORKS.md](HOW_IT_WORKS.md)** - Financial engine details
- **[EMAIL_TO_API_MAPPING.md](EMAIL_TO_API_MAPPING.md)** - Input field mapping
- **[PROOF_ITS_DYNAMIC.md](PROOF_ITS_DYNAMIC.md)** - Validation tests
- **[BUG_FIX_SUMMARY.md](BUG_FIX_SUMMARY.md)** - Recent bug fixes

## Testing

```bash
# Test the engine
python tests/test_underwriter.py

# Test the API (requires API running)
python tests/test_api.py
```

## What Makes This Different

**No templates!** Every number is calculated from your inputs using Excel formulas. Change any parameter → everything recalculates.

See [PROOF_ITS_DYNAMIC.md](PROOF_ITS_DYNAMIC.md) for technical validation.

---

Built for brokerages, PE firms, and REITs who need fast, accurate underwriting at scale.
