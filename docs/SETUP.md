# How to Run the CRE Underwriting Application

## Quick Start (3 steps)

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install packages
pip install -r backend/requirements.txt
```

### 2. Test the Underwriter Engine

```bash
# Run the core engine directly
cd backend
python cre_underwriter.py
```

This will create an Excel file at: `outputs/cre_underwriting.xlsx`

### 3. Start the API Server

```bash
# From the backend directory
python api.py
```

Server runs at: http://localhost:5001

## Using the Web Interface

1. Start the API server (step 3 above)
2. Open `frontend/underwriting_interface.html` in your browser
3. Fill out the form
4. Click "Generate Underwriting"
5. Download the Excel file

## Testing the API with curl

```bash
# Simple endpoint test
curl -X POST http://localhost:5001/underwrite/simple \
  -H "Content-Type: application/json" \
  -d '{
    "property_address": "120 Valleywood Drive",
    "tenant": "Sentrex Health Solutions Inc.",
    "area_sf": 60071,
    "current_rent_psf": 14.21,
    "lease_start": "03/01/2022",
    "lease_end": "02/29/2032",
    "annual_escalation": 3.0,
    "purchase_price": 17800000,
    "renewal_probability": 85,
    "market_rent_psf": 17.50,
    "market_escalation": 3.5,
    "vacancy_months": 8,
    "ti_psf": 5
  }' \
  --output test_underwriting.xlsx
```

## Running Tests

```bash
# Test the underwriter engine
python tests/test_underwriter.py

# Test the API (requires API to be running)
python tests/test_api.py
```

## Project Structure

```
underwriting_mvp/
├── backend/
│   ├── api.py                    # Flask API server
│   ├── cre_underwriter.py        # Core underwriting engine
│   └── requirements.txt          # Python dependencies
├── frontend/
│   └── underwriting_interface.html  # Web UI
├── tests/
│   ├── test_underwriter.py       # Engine tests
│   └── test_api.py               # API tests
├── outputs/                      # Generated Excel files
├── docs/                         # Documentation
└── venv/                         # Virtual environment (created by you)
```

## Troubleshooting

**Port 5000 in use?**
- Port changed to 5001 in the code
- Or edit `backend/api.py` line 191 to use a different port

**Dependencies not installing?**
- Make sure you're in the activated venv: `source venv/bin/activate`
- Check Python version: `python --version` (needs 3.8+)

**Excel file not opening?**
- Make sure you have Excel, LibreOffice, or Google Sheets
- File is saved in `outputs/` directory
