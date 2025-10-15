"""
Test suite for CRE Underwriter
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from cre_underwriter import CREUnderwriter

def test_basic_underwriting():
    """Test basic underwriting generation"""

    property_data = {
        'property_name': 'Test Property',
        'address': '123 Test St',
        'purchase_price': 10000000,
        'property_type': 'Industrial'
    }

    lease_data = {
        'tenant_name': 'Test Tenant Inc.',
        'lease_start': '01/01/2024',
        'lease_end': '12/31/2033',
        'lease_term_years': 10,
        'current_annual_rent': 500000,
        'area_sf': 50000,
        'escalation_rate': 0.03
    }

    assumptions = {
        'valuation_date': 'January, 2026',
        'discount_rate': 0.08,
        'resale_rate': 0.08,
        'leveraged_cf_rate': 0.08,
        'leveraged_resale_rate': 0.08,
        'discount_method': 'Annual',
        'hold_period_years': 10,
        'residual_sale_date': 'December, 2035',
        'period_to_cap': '12 Months After Sale',
        'exit_cap_rate': 0.065,
        'gross_up_noi': 'No',
        'selling_costs': 0.00,
        'renewal_probability': 0.85,
        'market_rent_psf': 12.00,
        'market_escalation_rate': 0.035,
        'market_term_years': 5,
        'vacancy_months': 6,
        'tenant_improvements_psf': 5,
        'leasing_commission_year1_pct': 0.08,
        'leasing_commission_subsequent_pct': 0.035
    }

    underwriter = CREUnderwriter()
    wb = underwriter.create_underwriting(property_data, lease_data, assumptions)

    # Verify sheets were created
    assert 'Valuation Summary' in wb.sheetnames
    assert 'Cash Flow' in wb.sheetnames
    assert 'Rent Schedule' in wb.sheetnames
    assert 'Market Leasing Summary' in wb.sheetnames

    print("✓ Basic underwriting test passed")
    return True

if __name__ == '__main__':
    test_basic_underwriting()
    print("\nAll tests passed!")
