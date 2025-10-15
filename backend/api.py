"""
CRE Underwriting API
Simple Flask API that receives deal parameters and returns underwriting package
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from cre_underwriter import CREUnderwriter
from datetime import datetime
import os
import tempfile

app = Flask(__name__)
CORS(app)  # Enable CORS for web interface

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "CRE Underwriting API"})

@app.route('/underwrite', methods=['POST'])
def underwrite():
    """
    Main underwriting endpoint - accepts user-friendly format

    Example:
    {
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
    """
    try:
        data = request.json

        # Transform simple input to full format
        area = data['area_sf']
        annual_rent = data['current_rent_psf'] * area

        # Parse dates and calculate lease term
        from datetime import datetime
        lease_start = datetime.strptime(data['lease_start'], '%m/%d/%Y')
        lease_end = datetime.strptime(data['lease_end'], '%m/%d/%Y')
        lease_term_years = (lease_end - lease_start).days / 365.25

        # Build complete data structures
        property_data = {
            'property_name': data.get('property_address', 'Property'),
            'address': data.get('property_address', ''),
            'purchase_price': data['purchase_price'],
            'property_type': data.get('property_type', 'Industrial')
        }

        lease_data = {
            'tenant_name': data['tenant'],
            'lease_start': data['lease_start'],
            'lease_end': data['lease_end'],
            'lease_term_years': int(lease_term_years),
            'current_annual_rent': annual_rent,
            'area_sf': area,
            'escalation_rate': data['annual_escalation'] / 100
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
            'exit_cap_rate': data.get('exit_cap_rate', 6.5) / 100 if data.get('exit_cap_rate', 6.5) > 1 else data.get('exit_cap_rate', 0.065),
            'gross_up_noi': 'No',
            'selling_costs': 0.00,
            'renewal_probability': data['renewal_probability'] / 100,
            'market_rent_psf': data['market_rent_psf'],
            'market_escalation_rate': data['market_escalation'] / 100,
            'market_term_years': 5,
            'vacancy_months': data['vacancy_months'],
            'tenant_improvements_psf': data['ti_psf'],
            'leasing_commission_year1_pct': 0.08,
            'leasing_commission_subsequent_pct': 0.035
        }

        # Generate underwriting
        underwriter = CREUnderwriter()
        wb = underwriter.create_underwriting(property_data, lease_data, assumptions)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            wb.save(tmp.name)
            temp_path = tmp.name

        # Note: Formula recalculation happens automatically when opened in Excel
        # If you need server-side recalculation, you can add LibreOffice or similar

        # Send file
        return send_file(
            temp_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"underwriting_{property_data['property_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
