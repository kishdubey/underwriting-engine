"""
API Tests for CRE Underwriting API
Run with: python test_api.py
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    print("✓ Health check passed")

def test_simple_underwriting():
    """Test simple underwriting endpoint"""
    payload = {
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
    }

    response = requests.post(
        f"{BASE_URL}/underwrite/simple",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    # Save the file
    with open('/tmp/test_underwriting.xlsx', 'wb') as f:
        f.write(response.content)

    print("✓ Simple underwriting test passed")
    print("  Output saved to: /tmp/test_underwriting.xlsx")

def test_full_underwriting():
    """Test full underwriting endpoint"""
    payload = {
        "property": {
            "name": "Test Property",
            "address": "123 Test St",
            "purchase_price": 10000000,
            "type": "Industrial"
        },
        "lease": {
            "tenant_name": "Test Tenant Inc.",
            "lease_start": "01/01/2024",
            "lease_end": "12/31/2033",
            "current_annual_rent": 500000,
            "area_sf": 50000,
            "escalation_rate": 0.03
        },
        "assumptions": {
            "renewal_probability": 0.85,
            "market_rent_psf": 12.00,
            "market_escalation_rate": 0.035,
            "vacancy_months": 6,
            "tenant_improvements_psf": 5,
            "exit_cap_rate": 0.065
        }
    }

    response = requests.post(
        f"{BASE_URL}/underwrite",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200
    print("✓ Full underwriting test passed")

if __name__ == '__main__':
    print("Testing CRE Underwriting API...")
    print("Make sure the API is running: python api.py\n")

    try:
        test_health()
        test_simple_underwriting()
        test_full_underwriting()
        print("\n✅ All API tests passed!")
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API. Make sure it's running on port 5000")
        sys.exit(1)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
