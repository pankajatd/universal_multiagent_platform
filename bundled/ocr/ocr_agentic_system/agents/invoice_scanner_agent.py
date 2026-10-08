"""
Invoice & Receipt Scanner Agent:
Specialist agent for automated accounting, ERP data entry, and expense management.
Extracts vendor details, invoice numbers, line items, tax, and totals,
and performs rigorous mathematical consistency validation.
"""
import re
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger("InvoiceScannerAgent")

class InvoiceScannerAgent:
    def __init__(self):
        # Regular expressions for key financial entities
        self.invoice_num_regex = re.compile(
            r'(?:invoice|inv|receipt|bill|order|ticket)\s*(?:no\.?|#|number|id)?[:\s]*([a-z0-9\-]+)', 
            re.IGNORECASE
        )
        self.date_regex = re.compile(
            r'(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b|\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\b)'
        )
        self.total_regex = re.compile(
            r'(?:grand\s+total|total\s+amount|balance\s+due|net\s+total|amount\s+due|total)[:\s]*\$?\s*([0-9]+(?:\.[0-9]{2})?)', 
            re.IGNORECASE
        )
        self.subtotal_regex = re.compile(
            r'(?:subtotal|sub-total|sub\s+total)[:\s]*\$?\s*([0-9]+(?:\.[0-9]{2})?)', 
            re.IGNORECASE
        )
        self.tax_regex = re.compile(
            r'(?:tax|vat|gst|sales\s+tax)[:\s]*\$?\s*([0-9]+(?:\.[0-9]{2})?)', 
            re.IGNORECASE
        )
        self.currency_regex = re.compile(r'([$€£]|USD|EUR|GBP|CAD|INR|AUD)')

    def process_invoice(self, raw_boxes: List[Dict[str, Any]], full_text: str) -> Tuple[Dict[str, Any], List[str]]:
        """
        Extracts structured accounting fields from OCR boxes and raw text.
        Performs mathematical integrity validation on line items, tax, and total.
        Returns:
            (extracted_invoice_dict, validation_errors_list)
        """
        validation_errors: List[str] = []

        lines = [b.get("text", "").strip() for b in raw_boxes if b.get("text", "").strip()]
        if not lines and full_text.strip():
            lines = [l.strip() for l in full_text.splitlines() if l.strip()]

        if not lines:
            validation_errors.append("No text extracted from the invoice/receipt image.")
            return {"document_type": "invoice", "vendor_name": "UNKNOWN"}, validation_errors

        # 1. Vendor Name: Usually the first non-generic heading line
        vendor_name = "Unknown Vendor"
        for line in lines[:5]:
            # skip lines that are just numbers or known invoice labels
            if len(line) > 2 and not any(kw in line.lower() for kw in ["invoice", "receipt", "date", "bill to", "tax"]):
                vendor_name = line
                break

        # 2. Currency detection
        curr_match = self.currency_regex.search(full_text)
        currency = curr_match.group(1) if curr_match else "$"

        # 3. Invoice Number
        inv_match = self.invoice_num_regex.search(full_text)
        invoice_number = inv_match.group(1) if inv_match else "INV-AUTO-DETECTED"

        # 4. Dates
        date_match = self.date_regex.search(full_text)
        invoice_date = date_match.group(1) if date_match else "N/A"

        # 5. Extract Totals (Subtotal, Tax, Grand Total)
        subtotal: Optional[float] = None
        tax: Optional[float] = None
        grand_total: Optional[float] = None

        # Iterate reverse through lines to find bottom financial totals
        for line in reversed(lines):
            line_clean = line.replace(",", "")
            
            if grand_total is None:
                tot_m = self.total_regex.search(line_clean)
                if tot_m:
                    try:
                        grand_total = float(tot_m.group(1))
                    except ValueError:
                        pass

            if subtotal is None:
                sub_m = self.subtotal_regex.search(line_clean)
                if sub_m:
                    try:
                        subtotal = float(sub_m.group(1))
                    except ValueError:
                        pass

            if tax is None:
                tax_m = self.tax_regex.search(line_clean)
                if tax_m:
                    try:
                        tax = float(tax_m.group(1))
                    except ValueError:
                        pass

        # 6. Extract Line Items (e.g. "Widget A  2  15.00  30.00")
        line_items = []
        item_regex = re.compile(r'^([A-Za-z0-9\s\-_]+?)\s+(\d+)\s+([0-9]+\.[0-9]{2})\s+([0-9]+\.[0-9]{2})$')
        
        for line in lines:
            m = item_regex.match(line.strip())
            if m:
                desc = m.group(1).strip()
                qty = int(m.group(2))
                unit_p = float(m.group(3))
                tot_p = float(m.group(4))
                line_items.append({
                    "description": desc,
                    "quantity": qty,
                    "unit_price": unit_p,
                    "line_total": tot_p
                })

        # Heuristic fallback if standard line items regex did not catch all: look for simple price endings
        if not line_items:
            price_line_regex = re.compile(r'([A-Za-z0-9\s]+?)\s+[$]?([0-9]+\.[0-9]{2})$')
            for line in lines:
                # ignore totals
                if any(kw in line.lower() for kw in ["total", "subtotal", "tax", "vat", "balance", "amount"]):
                    continue
                m = price_line_regex.match(line.strip())
                if m:
                    desc = m.group(1).strip()
                    price = float(m.group(2))
                    line_items.append({
                        "description": desc,
                        "quantity": 1,
                        "unit_price": price,
                        "line_total": price
                    })

        # 7. Fallback inferences if subtotal or tax are missing
        calculated_items_sum = round(sum(item["line_total"] for item in line_items), 2)
        if subtotal is None and line_items:
            subtotal = calculated_items_sum

        if grand_total is None:
            if subtotal is not None:
                tax_val = tax if tax is not None else 0.0
                grand_total = round(subtotal + tax_val, 2)

        if tax is None and subtotal is not None and grand_total is not None:
            diff = round(grand_total - subtotal, 2)
            if diff >= 0:
                tax = diff

        extracted_data = {
            "document_type": "invoice",
            "vendor_name": vendor_name,
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "currency": currency,
            "line_items": line_items,
            "financial_summary": {
                "subtotal": subtotal,
                "tax": tax if tax is not None else 0.0,
                "grand_total": grand_total
            },
            "line_items_count": len(line_items)
        }

        # 8. Mathematical Integrity Validation Rules
        if grand_total is None or grand_total <= 0:
            validation_errors.append("Missing or non-positive Grand Total. Failed financial extraction.")

        if subtotal is not None and tax is not None and grand_total is not None:
            expected_total = round(subtotal + tax, 2)
            if abs(expected_total - grand_total) > 0.05:
                validation_errors.append(
                    f"Mathematical Mismatch: Subtotal ({subtotal}) + Tax ({tax}) = {expected_total}, but Grand Total is {grand_total}."
                )

        if line_items and subtotal is not None:
            if abs(calculated_items_sum - subtotal) > 0.10:
                validation_errors.append(
                    f"Line Items Discrepancy: Sum of line items ({calculated_items_sum}) does not equal Subtotal ({subtotal})."
                )

        return extracted_data, validation_errors
