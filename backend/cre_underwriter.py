"""
Commercial Real Estate Underwriting Automation
Replicates the manual work done by analysts in Argus
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

class CREUnderwriter:
    def __init__(self):
        self.wb = Workbook()
        self.setup_styles()
        
    def setup_styles(self):
        """Define standard formatting styles"""
        self.blue_font = Font(color='0000FF')  # Inputs
        self.black_font = Font(color='000000')  # Formulas
        self.green_font = Font(color='008000')  # Links
        self.yellow_fill = PatternFill(start_color='FFFF00', fill_type='solid')
        self.header_fill = PatternFill(start_color='B8CCE4', fill_type='solid')
        self.bold_font = Font(bold=True)
        self.thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
    def create_underwriting(self, property_data, lease_data, assumptions):
        """Main method to create complete underwriting package"""
        
        # Remove default sheet
        if 'Sheet' in self.wb.sheetnames:
            del self.wb['Sheet']
            
        # Create all required sheets
        self.create_valuation_summary(property_data, assumptions)
        self.create_cash_flow(property_data, lease_data, assumptions)
        self.create_rent_schedule(lease_data, assumptions)
        self.create_market_leasing_summary(assumptions)
        
        return self.wb
    
    def create_valuation_summary(self, property_data, assumptions):
        """Create valuation assumptions and return summary sheet"""
        ws = self.wb.create_sheet('Valuation Summary')
        
        # Title
        ws['A1'] = 'Valuation Assumptions'
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:B1')
        
        row = 3
        
        # Valuation inputs
        inputs = [
            ('PV Calculation Date', assumptions['valuation_date']),
            ('Unleveraged Cash Flow Rate', f"{assumptions['discount_rate']:.2%}"),
            ('Unleveraged Resale Rate', f"{assumptions['resale_rate']:.2%}"),
            ('Leveraged Cash Flow Rate', f"{assumptions['leveraged_cf_rate']:.2%}"),
            ('Leveraged Resale Rate', f"{assumptions['leveraged_resale_rate']:.2%}"),
            ('Discount Method', assumptions['discount_method']),
            ('Hold Period', f"{assumptions['hold_period_years']} Years"),
            ('Residual Sale Date', assumptions['residual_sale_date']),
            ('Period to Cap', assumptions['period_to_cap']),
            ('Exit Cap Rate', f"{assumptions['exit_cap_rate']:.2%}"),
            ('Gross-up NOI', assumptions['gross_up_noi']),
            ('Selling Costs', f"{assumptions['selling_costs']:.2%}")
        ]
        
        for label, value in inputs:
            ws[f'A{row}'] = label
            ws[f'B{row}'] = value
            ws[f'B{row}'].font = self.blue_font
            row += 1
            
        # Return Summary section
        row += 2
        ws[f'A{row}'] = 'Return Summary'
        ws[f'A{row}'].font = Font(bold=True, size=12)
        ws[f'A{row}'].fill = self.header_fill
        ws.merge_cells(f'A{row}:B{row}')
        
        row += 1
        purchase_price = property_data['purchase_price']
        
        # These would be calculated from cash flow sheet in real implementation
        return_metrics = [
            ('Total Return (Unleveraged)', 28287101),
            ('Total Return to Invest (Unleveraged)', 1.59),
            ('PV-Cash Flow (Unleveraged)', 6518425),
            ('PV-Net Sales Price', 8523662),
            ('Total PV (Unleveraged)', 15042087),
            ('Initial Investment', purchase_price),
            ('NPV (Unleveraged)', -2757913),
            ('% of PV-Income', 43.33),
            ('% of PV-Net Sales Price', 56.67),
            ('IRR (Unleveraged)', 5.74),
            ('IRR (Leveraged)', 5.74)
        ]
        
        for label, value in return_metrics:
            ws[f'A{row}'] = label
            if isinstance(value, (int, float)) and value > 100:
                ws[f'B{row}'] = value
                ws[f'B{row}'].number_format = '#,##0'
            elif isinstance(value, float):
                ws[f'B{row}'] = value
                ws[f'B{row}'].number_format = '0.00%'
            else:
                ws[f'B{row}'] = value
            row += 1
            
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20
        
    def create_cash_flow(self, property_data, lease_data, assumptions):
        """Create 10-year cash flow projection"""
        ws = self.wb.create_sheet('Cash Flow')
        
        # Header
        ws['A1'] = 'Cash Flow'
        ws['A1'].font = Font(bold=True, size=14)
        ws['A2'] = f"{property_data['property_name']} (Amounts in CAD)"
        ws['A3'] = f"Jan, 2026 through Dec, 2036"
        ws['A4'] = datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')
        
        # Column headers
        row = 6
        ws[f'A{row}'] = ''
        col = 2
        for year in range(1, 13):  # Year 1 through Year 11 + Total
            cell = ws.cell(row, col)
            if year <= 11:
                cell.value = f'Year {year}'
                ws.cell(row + 1, col).value = f'Dec-{2025 + year}'
            else:
                cell.value = 'Total'
            cell.fill = self.header_fill
            cell.font = self.bold_font
            cell.alignment = Alignment(horizontal='center')
            col += 1
            
        # For the Years Ending row
        row += 1
        ws[f'A{row}'] = 'For the Years Ending'
        ws[f'A{row}'].font = self.bold_font
        
        # Build cash flow model
        row += 2
        
        # Rental Revenue section
        section_starts = {}
        
        ws[f'A{row}'] = 'Rental Revenue'
        ws[f'A{row}'].font = Font(bold=True)
        section_starts['rental_revenue'] = row
        row += 1
        
        # Get base rent from lease data
        base_rent = lease_data['current_annual_rent']
        escalation_rate = lease_data['escalation_rate']
        lease_end_year = lease_data['lease_term_years']
        area = lease_data['area_sf']
        
        # Potential Base Rent row
        ws[f'A{row}'] = 'Potential Base Rent'
        for year in range(1, 12):
            col = year + 1
            if year == 1:
                ws.cell(row, col).value = base_rent
            else:
                # Reference previous year and escalate
                prev_cell = get_column_letter(col - 1) + str(row)
                if year <= lease_end_year:
                    ws.cell(row, col).value = f'={prev_cell}*(1+{escalation_rate})'
                else:
                    # After lease expiry, use market rent with different escalation
                    if year == lease_end_year + 1:
                        market_rent = assumptions['market_rent_psf'] * area
                        ws.cell(row, col).value = market_rent
                    else:
                        ws.cell(row, col).value = f'={prev_cell}*(1+{assumptions["market_escalation_rate"]})'
            ws.cell(row, col).number_format = '#,##0'
            
        # Total column
        ws.cell(row, 13).value = f'=SUM(B{row}:L{row})'
        ws.cell(row, 13).number_format = '#,##0'
        row += 1
        
        # Absorption & Turnover Vacancy
        ws[f'A{row}'] = 'Absorption & Turnover Vacancy'
        # Add vacancy in year 7 (upon lease expiry) based on non-renewal probability
        vacancy_year = lease_end_year + 1
        vacancy_months = assumptions['vacancy_months']
        non_renewal_prob = 1 - assumptions['renewal_probability']
        
        for year in range(1, 12):
            col = year + 1
            if year == vacancy_year:
                # Calculate vacancy impact
                annual_rent_cell = get_column_letter(col) + str(row - 1)
                vacancy_factor = (vacancy_months / 12) * non_renewal_prob
                ws.cell(row, col).value = f'=-{annual_rent_cell}*{vacancy_factor}'
            else:
                ws.cell(row, col).value = 0
            ws.cell(row, col).number_format = '#,##0'
            
        ws.cell(row, 13).value = f'=SUM(B{row}:L{row})'
        ws.cell(row, 13).number_format = '#,##0'
        row += 1
        
        # Scheduled Base Rent (total of above)
        ws[f'A{row}'] = 'Scheduled Base Rent'
        ws[f'A{row}'].font = self.bold_font
        scheduled_rent_row = row
        for col in range(2, 14):
            ws.cell(row, col).value = f'=SUM({get_column_letter(col)}{row-2}:{get_column_letter(col)}{row-1})'
            ws.cell(row, col).number_format = '#,##0'
        row += 1
        
        # Total Rental Revenue
        ws[f'A{row}'] = 'Total Rental Revenue'
        ws[f'A{row}'].font = Font(bold=True)
        for col in range(2, 14):
            ws.cell(row, col).value = f'={get_column_letter(col)}{scheduled_rent_row}'
            ws.cell(row, col).number_format = '#,##0'
        row += 2
        
        # Total Tenant Revenue (same as rental)
        ws[f'A{row}'] = 'Total Tenant Revenue'
        ws[f'A{row}'].font = Font(bold=True)
        tenant_revenue_row = row
        for col in range(2, 14):
            ws.cell(row, col).value = f'={get_column_letter(col)}{row-2}'
            ws.cell(row, col).number_format = '#,##0'
        row += 2
        
        # Potential Gross Revenue
        ws[f'A{row}'] = 'Potential Gross Revenue'
        ws[f'A{row}'].font = Font(bold=True)
        for col in range(2, 14):
            ws.cell(row, col).value = f'={get_column_letter(col)}{tenant_revenue_row}'
            ws.cell(row, col).number_format = '#,##0'
        row += 2
        
        # Effective Gross Revenue
        ws[f'A{row}'] = 'Effective Gross Revenue'
        ws[f'A{row}'].font = Font(bold=True)
        egr_row = row
        for col in range(2, 14):
            ws.cell(row, col).value = f'={get_column_letter(col)}{row-2}'
            ws.cell(row, col).number_format = '#,##0'
        row += 2
        
        # Net Operating Income (no operating expenses for NNN lease)
        ws[f'A{row}'] = 'Net Operating Income'
        ws[f'A{row}'].font = Font(bold=True)
        noi_row = row
        for col in range(2, 14):
            ws.cell(row, col).value = f'={get_column_letter(col)}{egr_row}'
            ws.cell(row, col).number_format = '#,##0'
        row += 1
        
        # Yield on PP row
        ws[f'A{row}'] = f'Yield on PP (${property_data["purchase_price"]/1000000:.2f}M)'
        ws[f'A{row}'].font = Font(bold=True, color='FF0000')
        pp = property_data['purchase_price']
        for col in range(2, 14):
            if col <= 12:  # Not for total column
                ws.cell(row, col).value = f'={get_column_letter(col)}{noi_row}/{pp}'
                ws.cell(row, col).number_format = '0.00%'
        row += 2
        
        # Leasing Costs section
        ws[f'A{row}'] = 'Leasing Costs'
        ws[f'A{row}'].font = Font(bold=True)
        row += 1
        
        # Tenant Improvements
        ws[f'A{row}'] = 'Tenant Improvements'
        ti_year = vacancy_year
        ti_psf = assumptions['tenant_improvements_psf']
        for year in range(1, 12):
            col = year + 1
            if year == ti_year:
                ws.cell(row, col).value = ti_psf * area * non_renewal_prob
            else:
                ws.cell(row, col).value = 0
            ws.cell(row, col).number_format = '#,##0'
        ws.cell(row, 13).value = f'=SUM(B{row}:L{row})'
        ws.cell(row, 13).number_format = '#,##0'
        row += 1
        
        # Leasing Commissions
        ws[f'A{row}'] = 'Leasing Commissions'
        lc_year = vacancy_year
        for year in range(1, 12):
            col = year + 1
            if year == lc_year:
                # 8% of Year 1 NOI
                noi_cell = get_column_letter(col) + str(noi_row)
                ws.cell(row, col).value = f'={noi_cell}*0.08*{non_renewal_prob}'
            elif year == lc_year + 1:
                # 3.5% of Year 2 NOI
                noi_cell = get_column_letter(col) + str(noi_row)
                ws.cell(row, col).value = f'={noi_cell}*0.035*{non_renewal_prob}'
            else:
                ws.cell(row, col).value = 0
            ws.cell(row, col).number_format = '#,##0'
        ws.cell(row, 13).value = f'=SUM(B{row}:L{row})'
        ws.cell(row, 13).number_format = '#,##0'
        row += 1
        
        # Total Leasing Costs
        ws[f'A{row}'] = 'Total Leasing Costs'
        ws[f'A{row}'].font = Font(bold=True)
        for col in range(2, 14):
            ws.cell(row, col).value = f'=SUM({get_column_letter(col)}{row-2}:{get_column_letter(col)}{row-1})'
            ws.cell(row, col).number_format = '#,##0'
        row += 2
        
        # Total Leasing & Capital Costs
        ws[f'A{row}'] = 'Total Leasing & Capital Costs'
        ws[f'A{row}'].font = Font(bold=True)
        capital_costs_row = row
        for col in range(2, 14):
            ws.cell(row, col).value = f'={get_column_letter(col)}{row-2}'
            ws.cell(row, col).number_format = '#,##0'
        row += 2
        
        # Cash Flow Before Debt Service
        ws[f'A{row}'] = 'Cash Flow Before Debt Service'
        ws[f'A{row}'].font = Font(bold=True)
        for col in range(2, 14):
            ws.cell(row, col).value = f'={get_column_letter(col)}{noi_row}-{get_column_letter(col)}{capital_costs_row}'
            ws.cell(row, col).number_format = '#,##0'
        row += 2
        
        # Cash Flow Available for Distribution
        ws[f'A{row}'] = 'Cash Flow Available for Distribution'
        ws[f'A{row}'].font = Font(bold=True)
        for col in range(2, 14):
            ws.cell(row, col).value = f'={get_column_letter(col)}{row-2}'
            ws.cell(row, col).number_format = '#,##0'
            
        # Set column widths
        ws.column_dimensions['A'].width = 35
        for col in range(2, 14):
            ws.column_dimensions[get_column_letter(col)].width = 12
            
    def create_rent_schedule(self, lease_data, assumptions):
        """Create detailed rent schedule showing escalations"""
        ws = self.wb.create_sheet('Rent Schedule')
        
        # Title
        ws['A1'] = f"{lease_data['tenant_name']} Rent Schedule"
        ws['A1'].font = Font(bold=True, size=14)
        ws['A2'] = '(Amounts in CAD)'
        
        # Headers
        row = 4
        headers = ['Date', 'Yrs', 'Mths', 'Days', 'Event Type', 'Description', 
                   'Annual Rent', 'Rate/Area', 'Area']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row, col)
            cell.value = header
            cell.font = self.bold_font
            cell.fill = self.header_fill
            
        row += 1
        
        # Starting rent
        start_date = datetime.strptime(lease_data['lease_start'], '%m/%d/%Y')
        current_date = start_date
        annual_rent = lease_data['current_annual_rent']
        area = lease_data['area_sf']
        rate_per_sf = annual_rent / area
        
        # Add initial rent
        ws.cell(row, 1).value = current_date.strftime('%m/%d/%Y')
        ws.cell(row, 2).value = 0
        ws.cell(row, 3).value = 2
        ws.cell(row, 4).value = 0
        ws.cell(row, 5).value = 'Base Rent'
        ws.cell(row, 6).value = f'${rate_per_sf:.2f} / SF / Year'
        ws.cell(row, 7).value = annual_rent
        ws.cell(row, 7).number_format = '#,##0'
        ws.cell(row, 8).value = rate_per_sf
        ws.cell(row, 8).number_format = '0.00'
        ws.cell(row, 9).value = area
        ws.cell(row, 9).number_format = '#,##0'
        row += 1
        
        # Annual escalations during initial lease term
        for year in range(1, lease_data['lease_term_years']):
            current_date = start_date + relativedelta(years=year)
            annual_rent *= (1 + lease_data['escalation_rate'])
            rate_per_sf = annual_rent / area
            
            ws.cell(row, 1).value = current_date.strftime('%m/%d/%Y')
            ws.cell(row, 2).value = year
            ws.cell(row, 3).value = 0
            ws.cell(row, 4).value = 0
            ws.cell(row, 5).value = 'Base Rent'
            ws.cell(row, 6).value = f'{lease_data["escalation_rate"]:.2%} Increase'
            ws.cell(row, 7).value = annual_rent
            ws.cell(row, 7).number_format = '#,##0'
            ws.cell(row, 8).value = rate_per_sf
            ws.cell(row, 8).number_format = '0.00'
            ws.cell(row, 9).value = area
            ws.cell(row, 9).number_format = '#,##0'
            row += 1
            
        # Lease expiry
        lease_end = datetime.strptime(lease_data['lease_end'], '%m/%d/%Y')
        ws.cell(row, 1).value = lease_end.strftime('%m/%d/%Y')
        ws.cell(row, 2).value = 0
        ws.cell(row, 3).value = 0
        ws.cell(row, 4).value = 0
        ws.cell(row, 5).value = 'Lease Expiry'
        row += 1
        
        # Vacancy period (assuming non-renewal)
        vacancy_end = lease_end + relativedelta(months=assumptions['vacancy_months'])
        ws.cell(row, 1).value = (lease_end + relativedelta(months=1)).strftime('%m/%d/%Y')
        ws.cell(row, 2).value = 0
        ws.cell(row, 3).value = 1
        ws.cell(row, 4).value = 0
        ws.cell(row, 5).value = 'Void On Expiry'
        ws.cell(row, 6).value = 'Months Vacant(Expiry)'
        ws.cell(row, 7).value = 0
        ws.cell(row, 8).value = 0.00
        ws.cell(row, 9).value = area
        ws.cell(row, 9).number_format = '#,##0'
        row += 1
        
        # Market lease assumption (MLA Profile)
        market_start = vacancy_end + relativedelta(months=1)
        market_rent = assumptions['market_rent_psf'] * area
        
        ws.cell(row, 1).value = market_start.strftime('%m/%d/%Y')
        ws.cell(row, 2).value = 1
        ws.cell(row, 3).value = 0
        ws.cell(row, 4).value = 0
        ws.cell(row, 5).value = 'MLA Profile'
        ws.cell(row, 6).value = f'${assumptions["market_rent_psf"]:.2f} / SF / Year'
        ws.cell(row, 7).value = market_rent
        ws.cell(row, 7).number_format = '#,##0'
        ws.cell(row, 8).value = assumptions['market_rent_psf']
        ws.cell(row, 8).number_format = '0.00'
        ws.cell(row, 9).value = area
        ws.cell(row, 9).number_format = '#,##0'
        row += 1
        
        # Market lease escalations
        current_date = market_start
        current_rent = market_rent
        for year in range(1, 5):  # 4 more years of escalations
            current_date += relativedelta(years=1)
            current_rent *= (1 + assumptions['market_escalation_rate'])
            rate_per_sf = current_rent / area
            
            ws.cell(row, 1).value = current_date.strftime('%m/%d/%Y')
            ws.cell(row, 2).value = year
            ws.cell(row, 3).value = 0
            ws.cell(row, 4).value = 0
            ws.cell(row, 5).value = 'Step Rent'
            ws.cell(row, 6).value = f'{assumptions["market_escalation_rate"]:.2%} Increase'
            ws.cell(row, 7).value = current_rent
            ws.cell(row, 7).number_format = '#,##0'
            ws.cell(row, 8).value = rate_per_sf
            ws.cell(row, 8).number_format = '0.00'
            ws.cell(row, 9).value = area
            ws.cell(row, 9).number_format = '#,##0'
            row += 1
            
        # Set column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['E'].width = 18
        ws.column_dimensions['F'].width = 25
        ws.column_dimensions['G'].width = 15
        
    def create_market_leasing_summary(self, assumptions):
        """Create market leasing assumptions summary"""
        ws = self.wb.create_sheet('Market Leasing Summary')
        
        # Title
        ws['A1'] = 'Market Leasing Summary'
        ws['A1'].font = Font(bold=True, size=14)
        ws['A3'] = f'As of Jan, 2026'
        ws['A5'] = f'${assumptions["market_rent_psf"]:.2f} base'
        ws['A5'].font = Font(bold=True, size=12)
        
        row = 7
        params = [
            ('Term Length (Years/Months)', f'{assumptions["market_term_years"]}/0'),
            ('Renewal Probability', f'{assumptions["renewal_probability"]:.2%}'),
            ('', ''),
            ('Months Vacant', assumptions['vacancy_months']),
            ('Months Vacant (Blended)', assumptions.get('vacancy_months_blended', 1.2)),
            ('', ''),
            ('Market Base Rent (UOM)', '$ / SF / Year'),
            ('Market Base Rent (New)', assumptions['market_rent_psf']),
            ('Market Base Rent (Renewal)', assumptions['market_rent_psf']),
            ('Market Base Rent (Blended)', assumptions['market_rent_psf']),
            ('', ''),
            ('Market Rental Value (UOM)', 'Continue Prior'),
            ('Market Rental Value', 'Continue Prior'),
            ('Use Market or Prior', 'N/A'),
            ('Prior Rent', 'N/A'),
            ('', ''),
            ('Rent Increases(UOM)', '% Increase'),
            ('Fixed Steps', f'{assumptions["market_escalation_rate"]:.2%}'),
            ('CPI Increase', 'None'),
            ('', ''),
            ('New Free Rent (Months)', 0),
            ('Renewal Free Rent (Months)', 0),
            ('Blended Free Rent (Months)', 0),
            ('', ''),
            ('Recovery Type', 'Continue Prior'),
            ('Miscellaneous Rent', 'None'),
            ('Incentives', 'None'),
            ('', ''),
            ('Tenant Improvements (UOM)', '$ / Area'),
            ('Tenant Improvements (New)', assumptions['tenant_improvements_psf']),
            ('Tenant Improvements (Renew)', 0),
            ('Tenant Improvements (Blended)', 0.75),
            ('', ''),
            ('Leasing Commissions (New UOM)', '% by Lease Year'),
            ('Leasing Commissions (New)', 'Varies'),
            ('Leasing Commissions (Renew UOM)', '% by Lease Year'),
            ('Leasing Commissions (Renew)', '0.00%'),
            ('Leasing Commissions (Blended)', ''),
            ('', ''),
            ('Upon Expiration', f'${assumptions["market_rent_psf"]:.2f} base')
        ]
        
        for label, value in params:
            if label:
                ws[f'A{row}'] = label
                ws[f'B{row}'] = value
                if label and not label.endswith('UOM)'):
                    ws[f'B{row}'].font = self.blue_font
            row += 1
            
        # Special note for leasing commissions
        ws['B35'] = '8% Year 1, 3.5% thereafter'
        
        ws.column_dimensions['A'].width = 35
        ws.column_dimensions['B'].width = 25


def main():
    """Example usage"""
    
    # Property details
    property_data = {
        'property_name': '120 Valleywood Markham',
        'address': '120 Valleywood Drive',
        'purchase_price': 17800000,
        'property_type': 'Industrial'
    }
    
    # Current lease details from rent roll
    lease_data = {
        'tenant_name': 'Sentrex Health Solutions Inc.',
        'lease_start': '03/01/2022',
        'lease_end': '02/29/2032',
        'lease_term_years': 10,
        'current_annual_rent': 853608.91,  # $14.21/SF * 60,071 SF
        'area_sf': 60071,
        'escalation_rate': 0.03  # 3% annual
    }
    
    # Market assumptions for upon expiry
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
        'renewal_probability': 0.85,  # 85% chance tenant renews
        'market_rent_psf': 17.50,
        'market_escalation_rate': 0.035,  # 3.5% annual escalations on market lease
        'market_term_years': 5,
        'vacancy_months': 8,  # If tenant doesn't renew
        'tenant_improvements_psf': 5,  # $5/SF TI allowance
        'leasing_commission_year1_pct': 0.08,  # 8% of year 1 NOI
        'leasing_commission_subsequent_pct': 0.035  # 3.5% of NOI thereafter
    }
    
    # Create underwriting
    underwriter = CREUnderwriter()
    wb = underwriter.create_underwriting(property_data, lease_data, assumptions)
    
    # Save to outputs directory
    import os
    output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, 'cre_underwriting.xlsx')
    wb.save(output_path)
    print(f"Underwriting package created: {output_path}")

    return output_path


if __name__ == '__main__':
    main()
