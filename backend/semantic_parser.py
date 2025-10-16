"""
Semantic Document Parser using LLM
Extracts structured data from rent rolls, tax bills, and CAM expense documents
regardless of format variations.
"""

import ollama
import os
import json
from typing import Dict, List, Optional, Union
import pdfplumber
import openpyxl
from datetime import datetime


class SemanticDocumentParser:
    """
    LLM-powered document parser that understands context and semantics.
    Uses local Llama 3.2 3B via Ollama to extract structured data from varying document formats.
    """

    def __init__(self, model: str = "llama3.2:3b"):
        """
        Initialize semantic parser with local Ollama model.

        Args:
            model: Ollama model name (defaults to llama3.2:3b)
        """
        self.model = model
        # Test if Ollama is running and model is available
        try:
            ollama.list()
        except Exception as e:
            raise ValueError(f"Ollama not available. Make sure it's running: {e}")

    def classify_document(self, document_text: str) -> str:
        """
        Classify the document type using LLM.

        Args:
            document_text: Raw text extracted from document

        Returns:
            Document type: 'rent_roll', 'tax_bill', 'cam_expenses', or 'unknown'
        """
        prompt = f"""You are a document classifier for commercial real estate.

Classify this document as ONE of these types:

1. rent_roll - Primary indicator: "Tenancy Schedule", "Lease From", "Lease To", tenant names with lease dates and rent amounts
2. tax_bill - Primary indicator: "Tax Bill", "Assessment", "Property Tax", municipality information
3. cam_expenses - Primary indicator: ONLY operating expenses (utilities, maintenance, insurance) WITHOUT lease information
4. unknown - Doesn't match any of the above

Document excerpt:
{document_text[:2000]}

Classification (one word only):"""

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )

        classification = response['message']['content'].strip().lower()

        # Extract just the classification type from the response
        for doc_type in ['rent_roll', 'tax_bill', 'cam_expenses', 'unknown']:
            if doc_type in classification:
                return doc_type

        return 'unknown'

    def extract_rent_roll(self, document_text: str, table_data: list = None) -> Dict:
        """
        Extract rent roll data for multi-tenant properties using structured table extraction.
        If table_data is provided, use it for LLM mapping; otherwise, fallback to text.
        """
        if table_data:
            # Pass the table as JSON to the LLM for mapping
            prompt = f"""\nYou are a commercial real estate rent roll parser. You are given rent roll tables as JSON. Your job is to:\n1. Find the main tenancy schedule to identify: unit, tenant_name, area_sf, lease_start, lease_end, and current_rent_psf (from 'Annual Rent/Area').\n2. Find the 'Charge Schedules' table to locate CAM and Tax recoveries. Map the 'Annual/Area' value for the 'camrec' charge to `cam_psf` and 'taxrec' to `tax_psf`.\n3. Find the 'Rent Steps' table. Extract every future rent step into a `rent_steps` list.\n4. Use the full, complete tenant name.\n5. Return ONLY the following JSON structure:\n{{\n    \"property_address\": \"full property address\",\n    \"total_area_sf\": total rentable area in SF,\n    \"tenants\": [\n        {{\n            \"unit\": \"unit number\",\n            \"tenant_name\": \"COMPLETE tenant name\",\n            \"area_sf\": area in square feet,\n            \"current_rent_psf\": current annual rent per SF,\n            \"lease_start\": \"MM/DD/YYYY\",\n            \"lease_end\": \"MM/DD/YYYY\",\n            \"cam_psf\": CAM recovery per SF from 'Charge Schedules',\n            \"tax_psf\": Tax recovery per SF from 'Charge Schedules',\n            \"rent_steps\": [\n                {{\n                    \"start_date\": \"MM/DD/YYYY\",\n                    \"end_date\": \"MM/DD/YYYY\",\n                    \"rent_psf\": annual rent per SF for that period\n                }}\n            ]\n        }}\n    ]\n}}\n\nTable data:\n{json.dumps(table_data)[:6000]}\n\nIMPORTANT: Return ONLY valid JSON. Do NOT return Python code, explanations, or markdown. Only output the JSON object as specified above.\n"""
        else:
            # Fallback to text-based extraction (legacy)
            prompt = f"""\nYou are extracting data from a structured rent roll text.\n\nIMPORTANT RULES:\n1. Find the main tenancy schedule to identify: unit, tenant_name, area_sf, lease_start, lease_end, and current_rent_psf (from 'Annual Rent/Area').\n2. Find the 'Charge Schedules' table to locate CAM and Tax recoveries. Map the 'Annual/Area' value for the 'camrec' charge to `cam_psf` and 'taxrec' to `tax_psf`.\n3. Find the 'Rent Steps' table. Extract every future rent step into a `rent_steps` list.\n4. Use the full, complete tenant name.\n5. Return ONLY the following JSON structure:\n{{\n    \"property_address\": \"full property address\",\n    \"total_area_sf\": total rentable area in SF,\n    \"tenants\": [\n        {{\n            \"unit\": \"unit number\",\n            \"tenant_name\": \"COMPLETE tenant name\",\n            \"area_sf\": area in square feet,\n            \"current_rent_psf\": current annual rent per SF,\n            \"lease_start\": \"MM/DD/YYYY\",\n            \"lease_end\": \"MM/DD/YYYY\",\n            \"cam_psf\": CAM recovery per SF from 'Charge Schedules',\n            \"tax_psf\": Tax recovery per SF from 'Charge Schedules',\n            \"rent_steps\": [\n                {{\n                    \"start_date\": \"MM/DD/YYYY\",\n                    \"end_date\": \"MM/DD/YYYY\",\n                    \"rent_psf\": annual rent per SF for that period\n                }}\n            ]\n        }}\n    ]\n}}\n\nDocument:\n{document_text[:4000]}\n\nIMPORTANT: Return ONLY valid JSON. Do NOT return Python code, explanations, or markdown. Only output the JSON object as specified above.\n"""

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )
        json_text = response['message']['content'].strip()

        # Extract JSON from markdown code blocks if present
        if '```json' in json_text:
            json_text = json_text.split('```json')[1].split('```')[0].strip()
        elif '```' in json_text:
            json_text = json_text.split('```')[1].split('```')[0].strip()

        try:
            data = json.loads(json_text)
            return data
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Raw response: {json_text[:500]}")
            return {"error": "Failed to parse document", "raw_response": json_text}

    def extract_tax_bill(self, document_text: str) -> Dict:
        """
        Extract property tax information from tax bill.

        Returns structured tax data including assessment values, rates, and amounts.
        """
        prompt = f"""Extract property tax information from this tax bill.

Return a JSON object with this exact structure:
{{
  "property_address": "civic address from bill",
  "roll_number": "assessment roll number",
  "billing_date": "MM/DD/YYYY",
  "assessment_value": total assessed value (number),
  "assessment_breakdown": {{
    "commercial": assessed value for commercial portion,
    "industrial": assessed value for industrial portion,
    "other": other assessed values
  }},
  "tax_amounts": {{
    "municipal": municipal tax amount,
    "education": education tax amount,
    "total": total tax amount
  }},
  "due_dates": [
    {{"date": "MM/DD/YYYY", "amount": installment amount}}
  ]
}}

Document:
{document_text}

Return ONLY valid JSON, no explanations."""

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )

        json_text = response['message']['content'].strip()

        # Clean up JSON
        if '```json' in json_text:
            json_text = json_text.split('```json')[1].split('```')[0].strip()
        elif '```' in json_text:
            json_text = json_text.split('```')[1].split('```')[0].strip()

        try:
            data = json.loads(json_text)
            return data
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            return {"error": "Failed to parse tax bill", "raw_response": json_text}

    def extract_cam_expenses(self, document_text: str) -> Dict:
        """
        Extract CAM (Common Area Maintenance) expenses.

        Returns structured operating expense data by category.
        """
        prompt = f"""Extract ALL operating expense categories and amounts from this CAM expenses document.

Return a JSON object with this exact structure:
{{
  "year": tax/expense year,
  "total_area_sf": total area for expense allocation,
  "expenses": [
    {{
      "category": "expense category name",
      "amount": dollar amount (number),
      "per_sf": amount per square foot if calculable
    }}
  ],
  "subtotal": subtotal before admin fee,
  "admin_fee_pct": admin fee percentage (as decimal, e.g., 0.15 for 15%),
  "admin_fee_amount": admin fee dollar amount,
  "total": total expenses including admin fee,
  "total_per_sf": total per square foot
}}

Document:
{document_text}

Return ONLY valid JSON, no explanations."""

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )

        json_text = response['message']['content'].strip()

        # Clean up JSON
        if '```json' in json_text:
            json_text = json_text.split('```json')[1].split('```')[0].strip()
        elif '```' in json_text:
            json_text = json_text.split('```')[1].split('```')[0].strip()

        try:
            data = json.loads(json_text)
            return data
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            return {"error": "Failed to parse CAM expenses", "raw_response": json_text}

    def parse_file(self, file_path: str) -> Dict:
        """
        Parse any supported file type and extract structured data.
        For PDFs, extract tables as structured data for LLM mapping.
        """
        table_data = None
        if file_path.lower().endswith('.pdf'):
            document_text, table_data = self._extract_text_and_tables_from_pdf(file_path)
        elif file_path.lower().endswith(('.xlsx', '.xls')):
            document_text = self._extract_text_from_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")

        # Classify the document
        doc_type = self.classify_document(document_text)

        # Extract data based on type
        if doc_type == 'rent_roll':
            extracted_data = self.extract_rent_roll(document_text, table_data=table_data)
        elif doc_type == 'tax_bill':
            extracted_data = self.extract_tax_bill(document_text)
        elif doc_type == 'cam_expenses':
            extracted_data = self.extract_cam_expenses(document_text)
        else:
            extracted_data = {"error": "Unknown document type"}

        return {
            "document_type": doc_type,
            "file_path": file_path,
            "extracted_data": extracted_data
        }

    def _extract_text_and_tables_from_pdf(self, file_path: str):
        """
        Extract text and tables from PDF file.
        Returns (text, table_data) where table_data is a list of dicts (if tables found), else None.
        """
        text_parts = []
        all_tables = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract tables as structured data
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        # Convert table to list of dicts if header row is present
                        if len(table) > 1:
                            headers = [str(h).strip() if h else "" for h in table[0]]
                            for row in table[1:]:
                                row_dict = {headers[i]: (str(cell).strip() if cell else "") for i, cell in enumerate(row)}
                                all_tables.append(row_dict)
                        else:
                            # Table with no header row, just add as list
                            all_tables.append(table)
                # Also get regular text for context
                text = page.extract_text()
                if text:
                    text_parts.append(f"\n=== PAGE {page_num + 1} TEXT ===")
                    text_parts.append(text)

        text_content = "\n".join(text_parts)
        table_data = all_tables if all_tables else None
        return text_content, table_data

    def _extract_text_from_excel(self, file_path: str) -> str:
        """Extract all text from Excel file."""
        wb = openpyxl.load_workbook(file_path, data_only=True)
        text_parts = []

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            text_parts.append(f"=== Sheet: {sheet_name} ===")

            for row in ws.iter_rows(values_only=True):
                row_text = []
                for cell in row:
                    if cell is not None:
                        if isinstance(cell, datetime):
                            row_text.append(cell.strftime('%m/%d/%Y'))
                        else:
                            row_text.append(str(cell))

                if row_text:
                    text_parts.append(" | ".join(row_text))

        wb.close()
        return "\n".join(text_parts)


def parse_multiple_documents(file_paths: List[str], model: str = "llama3.2:3b") -> Dict:
    """
    Parse multiple documents and combine the data.

    Args:
        file_paths: List of file paths to parse
        model: Ollama model name

    Returns:
        Combined data from all documents
    """
    parser = SemanticDocumentParser(model=model)

    results = {
        "rent_roll": None,
        "tax_bill": None,
        "cam_expenses": None,
        "unknown_docs": []
    }

    for file_path in file_paths:
        try:
            parsed = parser.parse_file(file_path)
            doc_type = parsed["document_type"]

            if doc_type == "rent_roll":
                results["rent_roll"] = parsed["extracted_data"]
            elif doc_type == "tax_bill":
                results["tax_bill"] = parsed["extracted_data"]
            elif doc_type == "cam_expenses":
                results["cam_expenses"] = parsed["extracted_data"]
            else:
                results["unknown_docs"].append({
                    "file": file_path,
                    "data": parsed
                })
        except Exception as e:
            results["unknown_docs"].append({
                "file": file_path,
                "error": str(e)
            })

    return results


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python semantic_parser.py <file_path> [model]")
        sys.exit(1)

    file_path = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "llama3.2:3b"

    parser = SemanticDocumentParser(model=model)
    result = parser.parse_file(file_path)

    print(json.dumps(result, indent=2))
