"""
Orchestrator Agent:
Analyzes the preprocessed image and raw OCR detection to classify document type
into one of three specialized domains:
1. Paper Document Digitizer (archiving, searching)
2. License Plate Recognition (smart traffic, ANPR/ALPR)
3. Invoice & Receipt Scanner (automated financial data entry)
Routes execution to the matching specialist agent.
"""
import re
from typing import Dict, Any, Tuple
from ..core.state import DocumentClass, TaskType
import logging

logger = logging.getLogger("OrchestratorAgent")

class OrchestratorAgent:
    def __init__(self):
        # Invoice keywords with high discrimination power
        self.invoice_keywords = [
            "invoice", "receipt", "bill", "tax", "vat", "gst", "total", 
            "subtotal", "amount", "qty", "quantity", "unit price", "balance due",
            "invoice number", "inv#", "payment", "merchant", "store"
        ]
        
        # License plate regex patterns (US, UK, EU, General standard)
        self.plate_regexes = [
            re.compile(r'^[A-Z]{1,3}[ -]?[0-9]{1,4}[ -]?[A-Z]{0,3}$', re.IGNORECASE),
            re.compile(r'^[0-9]{1,3}[ -]?[A-Z]{1,4}[ -]?[0-9]{0,3}$', re.IGNORECASE),
            re.compile(r'^[A-Z0-9]{5,9}$', re.IGNORECASE)
        ]

    def classify_and_route(
        self, 
        task_override: TaskType,
        raw_text: str, 
        dimensions: Dict[str, int],
        boxes_count: int
    ) -> Tuple[DocumentClass, float, str]:
        """
        Classifies the image and decides which agent should handle it.
        Returns:
            (classified_type, confidence_score, explanation_reason)
        """
        # 1. Check user override first
        if task_override and task_override != "auto":
            return task_override, 1.0, f"User explicitly selected task type '{task_override}'"

        text_lower = raw_text.lower()
        height = dimensions.get("height", 1)
        width = dimensions.get("width", 1)
        aspect_ratio = width / max(height, 1)

        # 2. Check for Invoice indicators
        matched_invoice_words = [kw for kw in self.invoice_keywords if kw in text_lower]
        has_currency = any(symbol in raw_text for symbol in ["$", "€", "£", "USD", "EUR", "GBP", "INR", "¥"])
        
        invoice_score = (len(matched_invoice_words) * 0.25) + (0.3 if has_currency else 0.0)
        
        # 3. Check for License Plate indicators
        # Typically plates have aspect ratio > 2.0 (e.g. 520x110 mm EU is 4.7, US is 2.0)
        # and very low box count (1 to 4 text boxes) and short character length (4 to 10 chars)
        clean_text_single_line = re.sub(r'[^A-Za-z0-9]', '', raw_text)
        is_plate_length = 4 <= len(clean_text_single_line) <= 11
        is_plate_aspect = aspect_ratio >= 1.8 or aspect_ratio <= 0.55
        few_boxes = boxes_count <= 4
        
        plate_regex_match = any(bool(r.match(clean_text_single_line)) for r in self.plate_regexes) if clean_text_single_line else False
        
        plate_score = 0.0
        if is_plate_aspect and is_plate_length and few_boxes:
            plate_score += 0.5
        if plate_regex_match:
            plate_score += 0.4
        if "plate" in text_lower or "traffic" in text_lower:
            plate_score += 0.2

        # 4. Check for Document indicators
        # Documents typically have multiple lines, high word count, standard paper ratio (~1.2 to 1.6)
        words = text_lower.split()
        doc_score = 0.0
        if len(words) > 20:
            doc_score += 0.4
        if 1.1 <= aspect_ratio <= 1.7 or 0.58 <= aspect_ratio <= 0.9: # portrait or landscape A4
            doc_score += 0.3
        if invoice_score < 0.3 and plate_score < 0.4:
            doc_score += 0.3

        # 5. Determine Winner
        scores = {
            "invoice": min(invoice_score, 1.0),
            "license_plate": min(plate_score, 1.0),
            "document": min(doc_score, 1.0)
        }

        winner = max(scores, key=scores.get)
        confidence = round(scores[winner], 2)

        # Fallback if all scores are low
        if confidence < 0.25:
            winner = "document"
            confidence = 0.50
            reason = "Ambiguous text features. Defaulting to general Document Digitizer agent."
        else:
            if winner == "invoice":
                reason = f"Detected financial keywords ({', '.join(matched_invoice_words[:4])}) with confidence {confidence}"
            elif winner == "license_plate":
                reason = f"Detected vehicle license plate geometry (ratio: {aspect_ratio:.2f}) and alphanumeric token '{clean_text_single_line}'"
            else:
                reason = f"Detected standard textual document structure with {len(words)} words and page layout"

        logger.info(f"Orchestrator routed image to [{winner.upper()}] - {reason}")
        return winner, confidence, reason
