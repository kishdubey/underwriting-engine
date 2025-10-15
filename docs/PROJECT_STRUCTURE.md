# Project Structure

```
underwriting_mvp/
├── backend/
│   ├── api.py                     # Flask REST API (1 endpoint)
│   ├── cre_underwriter.py         # Financial calculation engine
│   └── requirements.txt           # Python dependencies
│
├── frontend/
│   └── underwriting_interface.html # Web UI form
│
├── tests/
│   ├── test_api.py                # API endpoint tests
│   └── test_underwriter.py        # Engine unit tests
│
├── examples/
│   └── sample_request.json        # Example API request
│
├── outputs/                       # Generated Excel files
│   └── .gitkeep
│
├── venv/                          # Python virtual environment
│
├── .gitignore                     # Git ignore rules
│
├── README.md                      # Main documentation
│
├── CALCULATIONS_REFERENCE.md      # Every formula explained
├── EMAIL_TO_API_MAPPING.md        # Input field mapping
├── HOW_IT_WORKS.md                # Technical deep dive
├── PROOF_ITS_DYNAMIC.md           # Validation & testing
├── BUG_FIX_SUMMARY.md             # Recent fixes
│
├── BEFORE_AFTER_COMPARISON.md     # Use case analysis
└── QUICKSTART.md                  # Quick setup guide
```

## File Purposes

### Core Application
- **backend/api.py** - Single `/underwrite` endpoint
- **backend/cre_underwriter.py** - Generates Excel with formulas
- **frontend/underwriting_interface.html** - User-facing form

### Documentation
- **README.md** - Start here
- **CALCULATIONS_REFERENCE.md** - Complete formula documentation
- **HOW_IT_WORKS.md** - System architecture
- **QUICKSTART.md** - 3-step setup guide

### Technical References
- **PROOF_ITS_DYNAMIC.md** - Shows all calculations are dynamic
- **EMAIL_TO_API_MAPPING.md** - Maps broker email → API fields
- **BUG_FIX_SUMMARY.md** - Recent bug fixes
- **BEFORE_AFTER_COMPARISON.md** - Business case

## Getting Started

1. Read [README.md](README.md)
2. Follow [QUICKSTART.md](QUICKSTART.md)
3. See [examples/sample_request.json](examples/sample_request.json)
