# Email to API Input Mapping

## Original Broker Email Format:

```
"Rent roll attached – in place rent net rent is $14.21.
Lease escalates 3% annually until Feb 29 2032.
Upon lease expiry please use an 85% renewal probability,
tenant renewing at $17.50 net with 3.5% annual escalations.
In 15% probability they do not renew, assume 8 months downtime,
$5 TI, standard broker leasing commissions (8% net income year 1,
3.5% net income thereafter on a 5 year deal)."
```

## API Input Mapping:

| Email Text | API Field | Example Value |
|------------|-----------|---------------|
| "in place rent net rent is $14.21" | `current_rent_psf` | `14.21` |
| "Lease escalates 3% annually" | `annual_escalation` | `3.0` |
| "until Feb 29 2032" | `lease_end` | `"2/29/2032"` |
| "85% renewal probability" | `renewal_probability` | `85` |
| "tenant renewing at $17.50 net" | `market_rent_psf` | `17.50` |
| "3.5% annual escalations" | `market_escalation` | `3.5` |
| "8 months downtime" | `vacancy_months` | `8` |
| "$5 TI" | `ti_psf` | `5.0` |
| "8% net income year 1" | *(hardcoded)* | `0.08` |
| "3.5% net income thereafter" | *(hardcoded)* | `0.035` |

## Complete API Request:

```json
{
  "property_address": "120 Valleywood Drive",
  "tenant": "Sentrex Health Solutions Inc.",
  "area_sf": 60071,
  "current_rent_psf": 14.21,           ← "in place rent net rent is $14.21"
  "lease_start": "3/1/2022",           ← From rent roll
  "lease_end": "2/29/2032",            ← "until Feb 29 2032"
  "annual_escalation": 3.0,            ← "3% annually"
  "purchase_price": 17800000,          ← From broker
  "renewal_probability": 85,           ← "85% renewal probability"
  "market_rent_psf": 17.50,            ← "renewing at $17.50 net"
  "market_escalation": 3.5,            ← "3.5% annual escalations"
  "vacancy_months": 8,                 ← "8 months downtime"
  "ti_psf": 5.0                        ← "$5 TI"
}
```

## ✅ Perfect Match!

Every data point from the broker's email has a corresponding API field. The leasing commissions (8% year 1, 3.5% thereafter) are hardcoded in the engine as "standard broker leasing commissions."

## Missing from Email (but needed):

| API Field | Source | Why Needed |
|-----------|--------|------------|
| `property_address` | Rent roll | Identifying the property |
| `tenant` | Rent roll | Tenant name for schedule |
| `area_sf` | Rent roll | Calculate total rent from PSF |
| `lease_start` | Rent roll | Build escalation schedule |
| `purchase_price` | Broker's budget | Calculate yields and returns |

These are typically found in the attached rent roll or are provided separately by the broker.

## Web Form vs Email:

The web interface (`frontend/underwriting_interface.html`) collects all these fields in a simple form that mirrors exactly what the broker would write in an email - just structured!
