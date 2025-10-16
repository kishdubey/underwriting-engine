"""
CRE Underwriting API
Simple Flask API that receives deal parameters and returns underwriting package
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from cre_underwriter import CREUnderwriter
from excel_parser import parse_rent_roll, parse_rent_roll_flexible, parse_pdf_rent_roll, validate_parsed_data
from semantic_parser import SemanticDocumentParser, parse_multiple_documents
from datetime import datetime
import os
import tempfile
from werkzeug.utils import secure_filename
import logging

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('underwriting_api')

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
        "cam_psf": 5.07,
        "tax_psf": 2.17,
        "insurance_psf": 0.00,
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

        # Calculate base rent
        annual_rent = data['current_rent_psf'] * area

        # Calculate operating expense recoveries (for NNN leases)
        cam_annual = data.get('cam_psf', 0) * area
        tax_annual = data.get('tax_psf', 0) * area
        insurance_annual = data.get('insurance_psf', 0) * area
        total_recoveries = cam_annual + tax_annual + insurance_annual

        # Parse dates in multiple formats and calculate lease term
        from datetime import datetime
        
        def parse_date(date_str):
            """Parse date string in multiple formats"""
            formats = ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%Y/%m/%d']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date: {date_str}. Expected formats: MM/DD/YYYY, YYYY-MM-DD, MM-DD-YYYY, or YYYY/MM/DD")
        
        lease_start = parse_date(data['lease_start'])
        lease_end = parse_date(data['lease_end'])
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
            'escalation_rate': data['annual_escalation'] / 100,
            'cam_annual': cam_annual,
            'tax_annual': tax_annual,
            'insurance_annual': insurance_annual,
            'total_recoveries': total_recoveries,
            # NEW: Support for analyst-matching configurations
            'year1_starting_rent': data.get('year1_starting_rent'),
            'use_fractional_escalation': data.get('use_fractional_escalation', False)
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
            # NEW: month-level timing for vacancy and market rent (1-12)
            'vacancy_start_month': data.get('vacancy_start_month'),
            'market_rent_start_month': data.get('market_rent_start_month'),
            'tenant_improvements_psf': data['ti_psf'],
            'leasing_commission_year1_pct': data.get('leasing_commission_year1_pct', 8.0) / 100 if data.get('leasing_commission_year1_pct', 8.0) > 1 else data.get('leasing_commission_year1_pct', 0.08),
            'leasing_commission_subsequent_pct': data.get('leasing_commission_subsequent_pct', 3.5) / 100 if data.get('leasing_commission_subsequent_pct', 3.5) > 1 else data.get('leasing_commission_subsequent_pct', 0.035),
            # NEW: Support for analyst-matching configurations
            'adjusted_market_rent_psf': data.get('adjusted_market_rent_psf', data['market_rent_psf']),
            'use_fractional_escalation': data.get('use_fractional_escalation', False)
        }

        # Generate underwriting: validate dynamic assumptions first
        underwriter = CREUnderwriter()

        # Call return metrics calculation first to surface any missing dynamic inputs
        try:
            metrics_or_error = underwriter.calculate_return_metrics(property_data, lease_data, assumptions)
        except Exception as e:
            return jsonify({"error": f"Failed during validation: {str(e)}"}), 500

        # If the underwriter signals missing assumptions, forward to UI so it can prompt the user
        if isinstance(metrics_or_error, dict) and metrics_or_error.get('error') == 'needs_input':
            missing = metrics_or_error.get('missing_assumptions', [])
            logger.info(f"Missing dynamic assumptions requested by underwriter: {missing}")

            # Provide suggested defaults where reasonable
            suggested_defaults = {}
            if 'vacancy_start_month' in missing:
                suggested_defaults['vacancy_start_month'] = 3  # March is a common transition month
            if 'market_rent_start_month' in missing:
                suggested_defaults['market_rent_start_month'] = 4  # April follows March vacancy
            if 'vacancy_months' in missing:
                suggested_defaults['vacancy_months'] = 8

            return jsonify({
                'error': 'needs_input',
                'missing_assumptions': missing,
                'suggested_defaults': suggested_defaults,
                'message': 'Please provide the missing dynamic assumptions to continue.'
            }), 422

        # All good: create the full underwriting workbook
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

@app.route('/parse-documents', methods=['POST'])
def parse_documents():
    """
    Parse multiple documents using semantic LLM-based extraction.
    Handles rent rolls, tax bills, and CAM expenses in any format.

    Accepts multiple files and returns structured data for each.

    Example response:
    {
        "success": true,
        "rent_roll": {...},
        "tax_bill": {...},
        "cam_expenses": {...},
        "property_type": "multi_tenant" or "single_tenant"
    }
    """
    try:
        # Check if files were uploaded
        if 'files' not in request.files and 'file' not in request.files:
            return jsonify({"error": "No files uploaded"}), 400

        # Handle both single and multiple file uploads
        files = request.files.getlist('files') if 'files' in request.files else [request.files['file']]

        if not files or files[0].filename == '':
            return jsonify({"error": "No files selected"}), 400

        # Save all files temporarily
        temp_paths = []
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                suffix = os.path.splitext(filename)[1]

                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    file.save(tmp.name)
                    temp_paths.append(tmp.name)

        # Parse all documents using semantic parser with local Ollama
        try:
            results = parse_multiple_documents(temp_paths)
        except Exception as e:
            logger.error(f"Semantic parsing failed: {e}")
            # Clean up temp files
            for path in temp_paths:
                try:
                    os.unlink(path)
                except:
                    pass
            return jsonify({"error": f"Failed to parse documents: {str(e)}"}), 500

        # Clean up temp files
        for path in temp_paths:
            try:
                os.unlink(path)
            except:
                pass

        # Determine property type based on rent roll
        property_type = "single_tenant"
        if results.get("rent_roll") and "tenants" in results["rent_roll"]:
            num_tenants = len(results["rent_roll"]["tenants"])
            if num_tenants > 1:
                property_type = "multi_tenant"

        response = {
            "success": True,
            "property_type": property_type,
            "rent_roll": results.get("rent_roll"),
            "tax_bill": results.get("tax_bill"),
            "cam_expenses": results.get("cam_expenses"),
            "unknown_docs": results.get("unknown_docs", [])
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Document parsing error: {e}")
        return jsonify({"error": f"Failed to parse documents: {str(e)}"}), 500


@app.route('/parse-excel', methods=['POST'])
def parse_excel():
    """
    Parse Excel rent roll and return extracted data.
    User can then review/edit before generating underwriting.

    Upload Excel file, returns JSON with extracted fields:
    {
        "property_address": "...",
        "tenant": "...",
        "area_sf": 60071,
        "current_rent_psf": 14.21,
        "cam_psf": 5.07,
        "tax_psf": 2.17,
        ...
    }
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Validate file extension
        is_pdf = file.filename.lower().endswith('.pdf')
        is_excel = file.filename.lower().endswith(('.xlsx', '.xls'))

        if not (is_pdf or is_excel):
            return jsonify({"error": "File must be Excel (.xlsx, .xls) or PDF (.pdf)"}), 400

        # Save to temporary file with appropriate suffix
        filename = secure_filename(file.filename)
        suffix = '.pdf' if is_pdf else '.xlsx'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            file.save(tmp.name)
            temp_path = tmp.name

        # Parse using semantic parser for both PDF and Excel
        try:
            parser = SemanticDocumentParser()
            result = parser.parse_file(temp_path)
            lease_data = result.get('extracted_data', {})
        except Exception as e:
            os.unlink(temp_path)
            return jsonify({"error": f"Failed to parse file: {str(e)}"}), 500

        # Clean up temp file
        os.unlink(temp_path)

        # Validate extracted data
        is_valid, missing_fields = validate_parsed_data(lease_data)

        response = {
            "success": True,
            "data": lease_data,
            "is_complete": is_valid,
            "missing_fields": missing_fields
        }

        if not is_valid:
            response["message"] = f"Extracted data is incomplete. Missing: {', '.join(missing_fields)}. Please fill in manually."

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Failed to parse Excel: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
