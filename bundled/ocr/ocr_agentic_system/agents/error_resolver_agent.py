"""
Error Resolver / Self-Correction Agent:
Monitors validation results, diagnoses extraction errors, and implements
autonomous corrective actions:
1. Re-filtering image (adaptive thresholding, CLAHE, deskew, morphological cleanup)
2. Character-level ambiguity resolution ('O' vs '0', 'I' vs '1', 'S' vs '5')
3. Mathematical constraint reconciliation for invoices (decimal points, tax deduction)
4. Graceful fallback recovery to ensure workflow resilience without crashing.
"""
import re
from typing import Dict, Any, List, Tuple, Optional
from ..core.state import OCRWorkflowState, ErrorRecord
import logging

logger = logging.getLogger("ErrorResolverAgent")

class ErrorResolverAgent:
    def __init__(self):
        # OCR Confusable mappings: Digits -> Letters and Letters -> Digits
        self.char_to_digit = {'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1', 'Z': '2', 'S': '5', 'B': '8', 'G': '6'}
        self.digit_to_char = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B', '6': 'G'}

    def resolve(self, state: OCRWorkflowState) -> Tuple[Dict[str, Any], bool, Optional[str], str]:
        """
        Diagnoses validation errors and attempts self-correction.
        Returns:
            updated_data: repaired or modified extracted_data
            is_now_valid: True if error was resolved in-memory
            reprocess_strategy: Strategy name if image must be reprocessed by Preprocessor, or None
            diagnosis_log: Human-readable explanation of resolution applied
        """
        validation_errors = state.get("validation_errors", [])
        classified_type = state.get("classified_type", "document")
        extracted_data = dict(state.get("extracted_data", {}))
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)
        raw_text = state.get("full_raw_text", "")

        logger.warning(f"ErrorResolver invoked! Errors: {validation_errors}. Retry count: {retry_count}/{max_retries}")

        # If max retries already reached, perform best-effort fallback
        if retry_count >= max_retries:
            diagnosis = f"Max retries ({max_retries}) reached. Applying best-effort fallback reconciliation to continue workflow."
            extracted_data["error_resolution_status"] = "PARTIAL_RECOVERY_MAX_RETRIES_REACHED"
            return extracted_data, True, None, diagnosis

        # -------------------------------------------------------------
        # DOMAIN 1: LICENSE PLATE RESOLUTION
        # -------------------------------------------------------------
        if classified_type == "license_plate":
            plate = extracted_data.get("plate_number", "")
            
            # Check for low confidence or empty text -> request image color inversion or CLAHE
            if any("empty" in e.lower() or "low ocr confidence" in e.lower() for e in validation_errors):
                strategy = "invert_colors" if retry_count == 0 else "aggressive_clahe"
                diagnosis = f"Plate image exhibits poor contrast or dark background. Triggering image reprocessing with strategy: '{strategy}'."
                return extracted_data, False, strategy, diagnosis

            # Check for character ambiguities (e.g. O instead of 0 in numbers, or 0 instead of O in letters)
            # Example: Fix common UK standard pattern: 2 letters, 2 digits, 3 letters
            if len(plate) >= 6:
                repaired_plate = list(plate)
                has_repairs = False
                
                # If characters 2 and 3 should be digits (e.g. UK style AB02CDE)
                if len(plate) == 7:
                    for idx in [2, 3]:
                        if repaired_plate[idx] in self.char_to_digit:
                            repaired_plate[idx] = self.char_to_digit[repaired_plate[idx]]
                            has_repairs = True
                    for idx in [0, 1, 4, 5, 6]:
                        if repaired_plate[idx] in self.digit_to_char:
                            repaired_plate[idx] = self.digit_to_char[repaired_plate[idx]]
                            has_repairs = True

                # General standard: replace obvious noise like dots or underscores
                plate_clean = "".join(repaired_plate).replace(".", "").replace("-", "")
                
                if has_repairs or plate_clean != plate:
                    extracted_data["plate_number"] = plate_clean
                    extracted_data["original_unrepaired_plate"] = plate
                    extracted_data["character_ambiguity_correction_applied"] = True
                    diagnosis = f"Resolved optical character confusion: repaired plate from '{plate}' to '{plate_clean}' using syntax heuristics."
                    return extracted_data, True, None, diagnosis

            # If still failed, request binarize_otsu
            return extracted_data, False, "binarize_otsu", "Plate syntax unresolved. Triggering Otsu binarization for sharper letter contours."

        # -------------------------------------------------------------
        # DOMAIN 2: INVOICE & RECEIPT RESOLUTION
        # -------------------------------------------------------------
        elif classified_type == "invoice":
            fin_summary = dict(extracted_data.get("financial_summary", {}))
            subtotal = fin_summary.get("subtotal")
            tax = fin_summary.get("tax")
            grand_total = fin_summary.get("grand_total")
            line_items = extracted_data.get("line_items", [])

            # Check for Math Mismatches (e.g. Subtotal + Tax != Grand Total)
            for err in validation_errors:
                if "Mathematical Mismatch" in err or "Discrepancy" in err:
                    # Strategy A: Check if OCR omitted a decimal point (e.g. 10500 instead of 105.00)
                    if grand_total and subtotal:
                        if abs(grand_total / 100.0 - subtotal) < 20.0:
                            corrected_total = round(grand_total / 100.0, 2)
                            diagnosis = f"Detected OCR decimal point omission in Grand Total ({grand_total} -> {corrected_total}). Rebalanced accounting totals."
                            fin_summary["grand_total"] = corrected_total
                            extracted_data["financial_summary"] = fin_summary
                            return extracted_data, True, None, diagnosis

                    # Strategy B: If Subtotal and Tax are present and confident, recalculate Grand Total
                    if subtotal is not None and tax is not None:
                        corrected_total = round(subtotal + tax, 2)
                        diagnosis = f"Reconciled financial discrepancy: recomputed Grand Total from Subtotal ({subtotal}) + Tax ({tax}) = {corrected_total}."
                        fin_summary["grand_total"] = corrected_total
                        extracted_data["financial_summary"] = fin_summary
                        return extracted_data, True, None, diagnosis

                    # Strategy C: If Grand Total and Line Items are present, reconcile Subtotal
                    if line_items and grand_total is not None:
                        items_sum = round(sum(i["line_total"] for i in line_items), 2)
                        fin_summary["subtotal"] = items_sum
                        fin_summary["tax"] = round(max(grand_total - items_sum, 0.0), 2)
                        extracted_data["financial_summary"] = fin_summary
                        diagnosis = f"Reconciled subtotal from line items sum ({items_sum}) and inferred Tax ({fin_summary['tax']})."
                        return extracted_data, True, None, diagnosis

                elif "Missing or non-positive Grand Total" in err:
                    # Attempt to infer Grand Total from line items or subtotal
                    if line_items:
                        items_sum = round(sum(i["line_total"] for i in line_items), 2)
                        fin_summary["subtotal"] = items_sum
                        fin_summary["grand_total"] = items_sum
                        extracted_data["financial_summary"] = fin_summary
                        diagnosis = f"Inferred missing Grand Total ({items_sum}) from parsed line items sum."
                        return extracted_data, True, None, diagnosis
                    else:
                        # Image was likely too noisy/faded -> trigger aggressive CLAHE
                        strategy = "aggressive_clahe"
                        diagnosis = f"Invoice financial totals unreadable. Triggering contrast boost '{strategy}'."
                        return extracted_data, False, strategy, diagnosis

            # If other errors exist, trigger deskew or sharpening
            strategy = "sharpen_edges" if retry_count == 0 else "binarize_otsu"
            return extracted_data, False, strategy, f"Invoice extraction encountered validation issues. Re-processing with '{strategy}'."

        # -------------------------------------------------------------
        # DOMAIN 3: DOCUMENT DIGITIZATION RESOLUTION
        # -------------------------------------------------------------
        else: # document
            # Check if high noise / gibberish or low text
            if any("gibberish" in e.lower() or "insufficient" in e.lower() for e in validation_errors):
                # Clean up raw text directly
                cleaned_text = re.sub(r'[^a-zA-Z0-9\s.,?!:;\'"()-]', ' ', raw_text)
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                extracted_data["raw_text"] = cleaned_text
                extracted_data["total_word_count"] = len(re.findall(r'\b\w+\b', cleaned_text))
                
                # If still low word count, request image reprocessing
                if extracted_data["total_word_count"] < 8 and retry_count < max_retries:
                    strategy = "morphological_cleanup" if retry_count == 0 else "aggressive_clahe"
                    diagnosis = f"Document contains noise/speckles. Triggering morphological cleanup with '{strategy}'."
                    return extracted_data, False, strategy, diagnosis
                else:
                    diagnosis = "Sanitized OCR character stream and eliminated spurious non-text symbols."
                    return extracted_data, True, None, diagnosis

            # Generic image enhancement fallback
            strategy = "sharpen_edges"
            return extracted_data, False, strategy, f"Document quality validation failed. Applying '{strategy}'."
